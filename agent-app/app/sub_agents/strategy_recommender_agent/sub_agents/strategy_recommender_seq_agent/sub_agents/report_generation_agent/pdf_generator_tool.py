import json
import logging
import os
import re
from io import BytesIO
from typing import Any

import google.auth
from google.adk.tools import FunctionTool, ToolContext
from google.cloud import storage
from google.genai.types import Blob, Part
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    ListFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# The following import is commented out to avoid potential ImportError if not universally configured
# from app.utils.gcs import create_bucket_if_not_exists

_, project_id = google.auth.default()

os.environ.setdefault("GCS_RECOMMENDATION_BUCKET_NAME", "jarvis-agent")


def _get_gcs_client():
    """Initializes and returns a Google Cloud Storage client."""
    return storage.Client()


def _clean_strategy_string(strategy_str: Any) -> str:
    """
    Aggressively cleans and normalizes the strategy string for reliable comparison.
    Handles non-string inputs robustly by converting them to strings first.
    """

    # CRITICAL FIX: Ensure the input is a string before proceeding
    if not isinstance(strategy_str, str):
        if strategy_str is None:
            return "N/A"
        # Convert non-strings (like dicts, lists) to a string representation
        strategy_str = str(strategy_str)

    # 1. Remove non-printable characters and control characters
    cleaned = re.sub(r"[^\x20-\x7E]+", "", strategy_str)
    # 2. Strip standard whitespace and convert to upper case
    return cleaned.strip().upper()


def generate_and_save_pdf(json_report_string: str, tool_context: ToolContext) -> str:
    """
    Generates a PDF report from the final JSON strategy recommendation and
    saves it as an ADK artifact.
    """

    bucket_name = os.getenv("GCS_RECOMMENDATION_BUCKET_NAME")
    if not bucket_name:
        return "Error: GCS_RECOMMENDATION_BUCKET_NAME is not configured."

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    try:
        # 1. Strip all leading/trailing whitespace (including newlines)
        cleaned_json_string = json_report_string.strip()

        # 2. Check and strip non-standard/unwanted wrapping characters
        if cleaned_json_string.startswith("`") and cleaned_json_string.endswith("`"):
            cleaned_json_string = cleaned_json_string.strip("`")

        # Attempt the load
        report_data = json.loads(cleaned_json_string)
        logger.info("JSON REPORT DATA loaded successfully.")
        client_name = tool_context.state.get("client_name")
        if not client_name or client_name == "N/A":
            client_name = "Unknown_Client"

        # 2. --- PDF GENERATION LOGIC (Using ReportLab) ---
        pdf_buffer = BytesIO()

        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=letter,
            leftMargin=1 * inch,
            rightMargin=1 * inch,
            topMargin=1 * inch,
            bottomMargin=1 * inch,
        )

        styles = getSampleStyleSheet()

        # Define custom styles
        styles.add(
            ParagraphStyle(
                name="ReportTitle",
                fontName="Helvetica-Bold",
                fontSize=16,
                spaceAfter=20,
            )
        )
        styles.add(
            ParagraphStyle(
                name="SectionHeader",
                fontName="Helvetica-Bold",
                fontSize=12,
                spaceBefore=25,
                spaceAfter=0.25 * inch,
            )
        )
        styles.add(
            ParagraphStyle(
                name="StrategyTitle",
                fontName="Helvetica-Bold",
                fontSize=10,
                spaceBefore=10,
                spaceAfter=5,
            )
        )
        styles.add(
            ParagraphStyle(
                name="Justification", fontName="Helvetica", fontSize=10, spaceAfter=15
            )
        )
        styles.add(
            ParagraphStyle(
                name="MappingDetail",
                fontName="Helvetica",
                fontSize=9,
                leftIndent=0.5 * inch,
                spaceAfter=3,
            )
        )
        styles.add(
            ParagraphStyle(
                name="BulletPoint",
                fontName="Helvetica",
                fontSize=10,
                leftIndent=0.25 * inch,
                spaceAfter=12,
            )
        )
        styles.add(
            ParagraphStyle(
                name="SubBulletPoint",
                fontName="Helvetica",
                fontSize=10,
                leftIndent=0.75 * inch,
                spaceAfter=12,
            )
        )

        # --- NEW STYLES FOR TABLE ---

        styles.add(
            ParagraphStyle(
                name="TableCell", fontName="Helvetica", fontSize=9, leading=10
            )
        )
        styles.add(
            ParagraphStyle(
                name="TableHeader", fontName="Helvetica-Bold", fontSize=9, leading=10
            )
        )

        # Build the story (the list of elements to be placed in the PDF)
        story = []

        # Title
        title_text = f"Strategy Recommendation Report for {client_name}"
        story.append(Paragraph(title_text, styles["ReportTitle"]))

        # Executive Summary Header
        story.append(Paragraph("Executive Summary", styles["SectionHeader"]))
        story.append(Spacer(1, 0.1 * inch))

        # Executive Summary Content
        executive_summary = report_data.get("executive_summary", "N/A")
        story.append(Paragraph(executive_summary, styles["Justification"]))

        # --- START: Assessment Overview Section (New Combined Section) ---
        pain_points = report_data.get("pain_points", [])
        desired_outcomes = report_data.get("desired_outcomes", [])

        if pain_points or desired_outcomes:
            story.append(Paragraph("Assessment Overview", styles["SectionHeader"]))
            story.append(Spacer(1, 0.1 * inch))

            # 1. Render Pain Points
            if pain_points:
                # FINAL FIX: Hardcoding and using a dedicated variable ensures the string is Key Findings
                key_findings_header = "Key Findings:"

                story.append(
                    Paragraph(f"<b>{key_findings_header}</b>", styles["StrategyTitle"])
                )

                # Ensure the contents of the pain point list are stripped too
                pain_point_items = [
                    Paragraph(
                        point.strip() if isinstance(point, str) else point,
                        styles["BulletPoint"],
                    )
                    for point in pain_points
                ]
                story.append(
                    ListFlowable(
                        pain_point_items,
                        bulletAnchor="middle",
                        bulletkind="bullet",
                        leftIndent=0.25 * inch,
                        spaceAfter=10,
                    )
                )

            # 2. Render Desired Outcomes
            if desired_outcomes:
                story.append(
                    Paragraph(
                        "<b>Desired Business Outcomes:</b>", styles["StrategyTitle"]
                    )
                )  # Using StrategyTitle for bold subheading
                # Ensure the contents of the outcome list are stripped too
                outcome_items = [
                    Paragraph(
                        outcome.strip() if isinstance(outcome, str) else outcome,
                        styles["BulletPoint"],
                    )
                    for outcome in desired_outcomes
                ]
                story.append(
                    ListFlowable(
                        outcome_items,
                        bulletAnchor="middle",
                        bulletkind="bullet",
                        leftIndent=0.25 * inch,
                        spaceAfter=15,
                    )
                )
        # --- END: Assessment Overview Section ---

        # --- PHASE 1: PRE-PROCESS AND CATEGORIZE RECOMMENDATIONS ---

        migration_recos = []
        modernization_recos = []
        other_recos = []

        for r in report_data.get("recommendations", []):
            # USE THE AGGRESSIVE CLEANING HELPER FUNCTION
            strategy = _clean_strategy_string(r.get("strategy", "N/A"))
            if strategy in ["REPLATFORM", "REHOST"]:
                migration_recos.append(r)
            elif strategy == "REFACTOR":
                modernization_recos.append(r)
            else:
                other_recos.append(r)

        # --- PHASE 2: RENDER CATEGORIZED RECOMMENDATIONS ---

        # Dictionary for Justification Header Lookup (New Unbreakable Logic)
        JUSTIFICATION_HEADERS = {
            "Modernization Opportunities": "<b>Strategic Value of Modernization:</b>",
            "Migration Overview": "<b>Migration Target Options:</b>",
            "Other Strategy Recommendations": "<b>Justification:</b>",  # Default fallback for others
        }

        # Function to render a single recommendation block
        def render_recommendation(r, section_type):
            # --- GLOBAL TABLE SETTINGS FOR ROBUSTNESS (UNCHANGED) ---
            TABLE_SAFE_WIDTH = 6.0 * inch  # Guaranteed safe width for 6.5 inch frame
            MINIMAL_PADDING_STYLE = TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
            # --------------------------------------------------------

            cleaned_section_type = section_type.strip()
            strategy = _clean_strategy_string(r.get("strategy", "N/A"))
            justification_content = r.get("justification", [])
            pros_list = r.get("pros", [])
            cons_list = r.get("cons", [])

            justification_header = JUSTIFICATION_HEADERS.get(
                cleaned_section_type, "<b>Justification:</b>"
            )

            # Strategy Title
            story.append(Paragraph(f"Strategy: {strategy}", styles["StrategyTitle"]))

            # Justification Content Header
            story.append(Paragraph(justification_header, styles["StrategyTitle"]))

            # --- START: CORRECTED CONDITIONAL LOGIC ---

            table_rendered = False

            # 1. REFACTOR Table Logic (Independent IF)
            if (
                strategy == "REFACTOR"
                and isinstance(justification_content, list)
                and justification_content
                and isinstance(justification_content[0], dict)
                and "category" in justification_content[0]
            ):
                # ... [REFACTOR table setup code remains the same] ...
                refactor_headers = [
                    Paragraph("<b>Category</b>", styles["TableHeader"]),
                    Paragraph("<b>Current Implementation</b>", styles["TableHeader"]),
                    Paragraph("<b>Recommended GCP Service</b>", styles["TableHeader"]),
                    Paragraph("<b>Modernization Rationale</b>", styles["TableHeader"]),
                ]
                field_names = ["category", "current_impl", "gcp_service", "rationale"]

                proportional_widths = [0.18, 0.20, 0.25, 0.37]
                col_widths = [w * TABLE_SAFE_WIDTH for w in proportional_widths]

                table_data = [refactor_headers]
                for item in justification_content:
                    row = [
                        Paragraph(
                            item.get(field, "N/A").strip()
                            if isinstance(item.get(field, "N/A"), str)
                            else str(item.get(field, "N/A")),
                            styles["TableCell"],
                        )
                        for field in field_names
                    ]
                    table_data.append(row)

                table = Table(table_data, colWidths=col_widths)
                table.setStyle(MINIMAL_PADDING_STYLE)
                story.append(table)
                story.append(Spacer(1, 0.1 * inch))
                table_rendered = True  # Flag that a table was rendered

                # --- START: NEW IMPLEMENTATION STEPS SECTION (WITH LINK FIX) ---
                for item in justification_content:
                    steps = item.get("implementation_steps")
                    patterns = item.get("common_modernization_patterns")
                    category = item.get("category", "General")

                    if steps and isinstance(steps, list):
                        story.append(
                            Paragraph(f"<u>{category}</u>:", styles["StrategyTitle"])
                        )
                        story.append(Spacer(1, 0.1 * inch))

                        # Separate main steps from industry solutions (which contain the resolved links)
                        ref_start_index = -1
                        for i, step in enumerate(steps):
                            # The prompt mandates this header must be present for references
                            if (
                                "Relevant Industry Solutions & Customer Stories:"
                                in step.replace("*", "")
                            ):
                                ref_start_index = i
                                break

                        main_steps = (
                            steps[:ref_start_index] if ref_start_index != -1 else steps
                        )
                        ref_items = (
                            steps[ref_start_index + 1 :]
                            if ref_start_index != -1
                            else []
                        )

                        # 1. Render Main Implementation Steps
                        if main_steps:
                            for step in main_steps:
                                clean_step = step.strip()
                                if not clean_step or re.match(r"^\d+$", clean_step):
                                    continue  # Skip empty/numeric steps

                                # Check for "Phase X:" style headers, strip markdown, and make bold
                                if "phase" in clean_step.lower() and ":" in clean_step:
                                    header_text = clean_step.replace("*", "").strip()
                                    story.append(
                                        Paragraph(
                                            f"<b>{header_text}</b>",
                                            styles["StrategyTitle"],
                                        )
                                    )
                                elif re.match(r"^\d+\.\s", clean_step):
                                    # 1. Strip the markdown bolding (e.g., '**') from the original step
                                    text_without_markdown = clean_step.replace(
                                        "**", ""
                                    ).strip()

                                    # 2. Apply the bolding to the entire string (including the leading '1. ')
                                    # using ReportLab's HTML-like tag and the bolder style.
                                    story.append(
                                        Paragraph(
                                            f"<b>{text_without_markdown}</b>",
                                            styles["StrategyTitle"],
                                        )
                                    )
                                    # story.append(Paragraph(clean_step, styles['BulletPoint']))
                                elif re.match(r"^\s*[a-z]\.\s", clean_step):
                                    story.append(
                                        Paragraph(clean_step, styles["SubBulletPoint"])
                                    )
                                else:
                                    story.append(
                                        Paragraph(clean_step, styles["BulletPoint"])
                                    )
                                story.append(Spacer(1, 0.05 * inch))

                        # 2. Render Relevant Industry Solutions (with Hyperlinks)
                        if ref_items:
                            # Re-add the header if it was found and separated
                            story.append(
                                Paragraph(
                                    "<b>Relevant Industry Solutions & Customer Stories:</b>",
                                    styles["StrategyTitle"],
                                )
                            )

                            ref_paragraphs = []
                            final_link = None
                            for ref_item in ref_items:
                                clean_ref_item = ref_item.strip()
                                if "For more details, visit:" in clean_ref_item:
                                    final_link = clean_ref_item
                                elif clean_ref_item:
                                    ref_paragraphs.append(
                                        Paragraph(
                                            ref_item.strip(), styles["BulletPoint"]
                                        )
                                    )

                            if ref_paragraphs:
                                story.append(
                                    ListFlowable(
                                        ref_paragraphs,
                                        bulletAnchor="middle",
                                        bulletkind="bullet",
                                        leftIndent=0.25 * inch,
                                        spaceAfter=15,
                                    )
                                )

                            if final_link:
                                # 1. Extract the actual URL from the text (e.g., "For more details, visit: URL")
                                url_match = re.search(r"(https?://[^\s]+)", final_link)

                                if url_match:
                                    url = url_match.group(0)
                                    # 2. Extract the descriptive text (everything before the URL)
                                    description = final_link.split(url)[0].strip()

                                    # 3. Create the ReportLab hyperlink markup
                                    # This uses <link> tag for clickability and <u> for underline.
                                    hyperlink_markup = f'{description} <link href="{url}" color="blue"><u>{url}</u></link>'

                                    # 4. Append the formatted Paragraph
                                    story.append(
                                        Paragraph(
                                            hyperlink_markup, styles["Justification"]
                                        )
                                    )
                                else:
                                    # Fallback to the original text if URL extraction fails
                                    story.append(
                                        Paragraph(final_link, styles["Justification"])
                                    )

                    # 3. Render Common Modernization Patterns (Moved outside the 'if steps' block)
                    if patterns and isinstance(patterns, list):
                        story.append(Spacer(1, 0.1 * inch))
                        story.append(
                            Paragraph(
                                "<b>Common Modernization Patterns:</b>",
                                styles["StrategyTitle"],
                            )
                        )

                        pattern_paragraphs = []
                        for p in patterns:
                            if isinstance(p, dict) and "pattern" in p and "url" in p:
                                hyperlink_markup = f'<link href="{p["url"]}" color="blue"><u>{p["pattern"].strip()}</u></link>'
                                pattern_paragraphs.append(
                                    Paragraph(hyperlink_markup, styles["BulletPoint"])
                                )

                        story.append(
                            ListFlowable(
                                pattern_paragraphs,
                                bulletAnchor="middle",
                                bulletkind="bullet",
                                leftIndent=0.25 * inch,
                                spaceAfter=10,
                            )
                        )

                    story.append(
                        Spacer(1, 0.25 * inch)
                    )  # Space after each category's deep dive
                # --- END: NEW IMPLEMENTATION STEPS SECTION (WITH LINK FIX) ---

            # 2. REPLATFORM Table Logic (Independent IF)
            if (
                strategy == "REPLATFORM"
                and isinstance(justification_content, list)
                and justification_content
                and isinstance(justification_content[0], dict)
                and "migration_target" in justification_content[0]
            ):
                # ... [REPLATFORM table setup code remains the same] ...
                replatform_headers = [
                    Paragraph("<b>Migration Target</b>", styles["TableHeader"]),
                    Paragraph("<b>Description</b>", styles["TableHeader"]),
                    Paragraph("<b>Migration Effort</b>", styles["TableHeader"]),
                    Paragraph("<b>Key Benefits</b>", styles["TableHeader"]),
                ]
                field_names = [
                    "migration_target",
                    "description",
                    "effort",
                    "key_benefits",
                ]

                proportional_widths = [0.18, 0.30, 0.10, 0.42]
                col_widths = [w * TABLE_SAFE_WIDTH for w in proportional_widths]

                table_data = [replatform_headers]
                for item in justification_content:
                    row = []
                    for field in field_names:
                        cell_content = item.get(field, "N/A")
                        row.append(
                            Paragraph(str(cell_content).strip(), styles["TableCell"])
                        )
                    table_data.append(row)

                table = Table(table_data, colWidths=col_widths)
                table.setStyle(MINIMAL_PADDING_STYLE)

                story.append(table)
                story.append(Spacer(1, 0.1 * inch))
                table_rendered = True  # Flag that a table was rendered

            # 3. Fallback for Simple Lists (Conditional ELIF on render flag)
            if not table_rendered:
                if justification_content and isinstance(justification_content, list):
                    # Ensure the contents of the justification list are stripped too
                    justification_items = [
                        Paragraph(
                            point.strip() if isinstance(point, str) else point,
                            styles["BulletPoint"],
                        )
                        for point in justification_content
                    ]
                    story.append(
                        ListFlowable(
                            justification_items,
                            bulletAnchor="middle",
                            bulletkind="bullet",
                            leftIndent=0.25 * inch,
                            spaceAfter=5,
                        )
                    )
                else:
                    story.append(
                        Paragraph(str(justification_content), styles["Justification"])
                    )

            # Pros Section (Rest of the function remains the same)
            if pros_list and isinstance(pros_list, list) and pros_list:
                story.append(Paragraph("<b>Pros:</b>", styles["StrategyTitle"]))
                pros_items = [
                    Paragraph(
                        pro.strip() if isinstance(pro, str) else pro,
                        styles["BulletPoint"],
                    )
                    for pro in pros_list
                ]
                story.append(
                    ListFlowable(
                        pros_items,
                        bulletAnchor="middle",
                        bulletkind="bullet",
                        leftIndent=0.25 * inch,
                        spaceAfter=5,
                    )
                )

            # Cons Section
            if cons_list and isinstance(cons_list, list) and cons_list:
                story.append(Paragraph("<b>Cons:</b>", styles["StrategyTitle"]))
                cons_items = [
                    Paragraph(
                        con.strip() if isinstance(con, str) else con,
                        styles["BulletPoint"],
                    )
                    for con in cons_list
                ]
                story.append(
                    ListFlowable(
                        cons_items,
                        bulletAnchor="middle",
                        bulletkind="bullet",
                        leftIndent=0.25 * inch,
                        spaceAfter=15,
                    )
                )

            story.append(Spacer(1, 0.1 * inch))

            # --- END: CORRECTED CONDITIONAL LOGIC ---

            # --- PHASE 2: RENDER CATEGORIZED RECOMMENDATIONS ---

        # Define the rendering order and header names
        all_recos = [
            ("Migration Overview (REPLATFORM/REHOST)", migration_recos),
            ("Modernization Opportunities (REFACTOR)", modernization_recos),
            ("Other Strategy Recommendations", other_recos),
        ]

        if migration_recos or modernization_recos or other_recos:
            story.append(Paragraph("Strategy Recommendations", styles["ReportTitle"]))
            story.append(Spacer(1, 0.1 * inch))

        for section_title, recos_list in all_recos:
            if recos_list:
                # Add the main section header only if there are recommendations in that category
                story.append(Paragraph(section_title, styles["SectionHeader"]))
                story.append(Spacer(1, 0.1 * inch))

                # Render each individual recommendation block
                for r in recos_list:
                    # Pass the cleaner section title for Justification Header lookup
                    # We pass the cleaned title (e.g., "Migration Overview") to the render function
                    if section_title.startswith("Migration Overview"):
                        render_recommendation(r, "Migration Overview")
                    elif section_title.startswith("Modernization Opportunities"):
                        render_recommendation(r, "Modernization Opportunities")
                    else:
                        render_recommendation(r, "Other Strategy Recommendations")

        # --- Tech Stack Summary Table Section ---
        # FALLBACK LOGIC: Check 'tech_stack_summary' (preferred) then 'tech_stack_to_gcp_mapping' (legacy)
        is_summary = report_data.get("tech_stack_summary", [])
        is_mapping = report_data.get("tech_stack_to_gcp_mapping", [])
        tech_stack_data = is_summary or is_mapping

        if tech_stack_data:
            story.append(Paragraph("Technology Stack Summary", styles["SectionHeader"]))
            story.append(Spacer(1, 0.1 * inch))

            # --- Define Table Headers based on which key was used ---
            if is_summary:
                # Use the clean, standardized headers
                table_headers = [
                    Paragraph("<b>Technology/Tool Name</b>", styles["TableHeader"]),
                    Paragraph("<b>Version</b>", styles["TableHeader"]),
                    Paragraph("<b>Purpose/Role</b>", styles["TableHeader"]),
                    Paragraph("<b>EOL Status / Replacement</b>", styles["TableHeader"]),
                ]
                field_names = ["name", "version", "purpose", "eol_status"]
                col_widths = [1.6 * inch, 0.7 * inch, 2.5 * inch, 1.7 * inch]
            elif is_mapping:
                # Use headers that match the 'tech_stack_to_gcp_mapping' structure
                table_headers = [
                    Paragraph("<b>Technology</b>", styles["TableHeader"]),
                    Paragraph("<b>GCP Service</b>", styles["TableHeader"]),
                    Paragraph("<b>Reason/Role</b>", styles["TableHeader"]),
                    Paragraph("<b>Strategy</b>", styles["TableHeader"]),
                ]
                field_names = ["technology", "gcp_service", "reason", "strategy"]
                col_widths = [1.4 * inch, 1.4 * inch, 2.5 * inch, 1.2 * inch]

            # 2. Prepare Table Data (starting with headers)
            table_data = [table_headers]

            # 3. Populate Table Data from JSON
            for item in tech_stack_data:
                # Dynamically build the row based on the field names, aggressively stripping content
                row = [
                    # FIX: Only apply _clean_strategy_string (which uppercases) to the 'strategy' field if needed
                    Paragraph(
                        _clean_strategy_string(item.get(field, "N/A")),
                        styles["TableCell"],
                    )
                    if field == "strategy"
                    # For all other fields, safely convert to string and strip basic whitespace ONLY
                    else Paragraph(
                        str(item.get(field, "N/A")).strip(), styles["TableCell"]
                    )
                    for field in field_names
                ]
                table_data.append(row)

            # 4. Create the Table object
            table = Table(table_data, colWidths=col_widths)

            # 5. Define Table Style (borders, alignment, header look)

            table.setStyle(
                TableStyle(
                    [
                        (
                            "BACKGROUND",
                            (0, 0),
                            (-1, 0),
                            colors.lightgrey,
                        ),  # Header background
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),  # All cells grid
                        (
                            "VALIGN",
                            (0, 0),
                            (-1, -1),
                            "TOP",
                        ),  # Vertical align: TOP is better for multi-line cells
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),  # Left align all columns
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),  # Padding for header
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ]
                )
            )

            # 6. Add the table to the story
            story.append(table)
            story.append(Spacer(1, 0.2 * inch))

        else:
            # Fallback if no tech stack data is provided
            story.append(
                Paragraph(
                    "No specific technology stack summary provided in the report.",
                    styles["Justification"],
                )
            )
            story.append(Spacer(1, 0.2 * inch))

        # Build the PDF document from the story
        doc.build(story)
        # 3. Create the ADK Artifact (`Part` object)
        artifact = Part(
            inline_data=Blob(
                # Use the correct MIME type for PDF
                mime_type="application/pdf",
                data=pdf_buffer.getvalue(),
            )
        )

        # 4. Save the Artifact using ToolContext
        filename = f"{client_name.replace(' ', '_')}_Strategy_Report.pdf"
        version = tool_context.save_artifact(filename=filename, artifact=artifact)

        # --- Upload to GCS ---
        storage_client = _get_gcs_client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(filename)
        pdf_buffer.seek(0)
        blob.upload_from_string(pdf_buffer.getvalue(), content_type="application/pdf")

        public_url = f"https://storage.googleapis.com/{bucket_name}/{filename}"
        logger.info(f"Uploaded '{filename}' to public GCS bucket.")

        tool_context.state["report_generated"] = True
        tool_context.state["final_report_url"] = public_url
        tool_context.state["client_name"] = client_name

        return f"Successfully created the Strategy Recommendation Report. It is publicly accessible at: {public_url}"

    except json.JSONDecodeError:
        return "ERROR: Agent output was not valid JSON. Could not generate PDF. Please ensure the output is pure JSON and not wrapped in any extra text or backticks."
    except Exception as e:
        return f"ERROR: Failed to generate or save PDF. This usually indicates a structural error in the reportlab code, often due to an invalid style or table property. Specific error: {e}"


generate_and_save_pdf_tool = FunctionTool(func=generate_and_save_pdf)
