import json
import logging
import os
from io import BytesIO

import google.auth
from google.adk.tools import FunctionTool, ToolContext
from google.cloud import storage
from google.genai.types import Blob, Part
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch  # Using inch is cleaner for margins
from reportlab.platypus import (
    ListFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

_, project_id = google.auth.default()

os.environ.setdefault("GCS_RECOMMENDATION_BUCKET_NAME", "jarvis-agent")


def _get_gcs_client():
    """Initializes and returns a Google Cloud Storage client."""
    return storage.Client()


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
        # 1. Parse the JSON string output from the LLM
        report_data = json.loads(json_report_string)

        logger.info(f"JSON REPORT DATA '{report_data}'.")

        client_name = tool_context.state.get("client_name")
        if not client_name or client_name == "N/A":
            logger.warning(
                "Client name not found or is 'N/A'. Using default name 'Unknown_Client'."
            )
            client_name = "Unknown_Client"

        # 2. --- PDF GENERATION LOGIC ---
        # Instead of actually implementing reportlab here, the core concept is:

        # This is where you would use a library like reportlab to create the PDF
        # content in memory (e.g., a BytesIO object).

        # 2. --- PDF GENERATION LOGIC (Using ReportLab) ---
        pdf_buffer = BytesIO()

        # SimpleDocTemplate simplifies page setup and frame management
        # Use margins (left, right, top, bottom)
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
                spaceBefore=15,
                spaceAfter=5,
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
                name="BulletPoint",
                fontName="Helvetica",
                fontSize=10,
                leftIndent=0.25 * inch,
                spaceAfter=3,
            )
        )

        # Build the story (the list of elements to be placed in the PDF)
        story = []

        # Title
        title_text = f"Strategy Recommendation Report for {client_name}"
        story.append(Paragraph(title_text, styles["ReportTitle"]))

        # Executive Summary Header
        story.append(Paragraph("Executive Summary", styles["SectionHeader"]))

        # Executive Summary Content
        executive_summary = report_data.get("executive_summary", "N/A")
        story.append(Paragraph(executive_summary, styles["Justification"]))

        # Recommendations Header
        story.append(Paragraph("Strategy Recommendations", styles["SectionHeader"]))

        # Loop through recommendations
        for r in report_data.get("recommendations", []):
            strategy = r["strategy"].upper()
            justification_content = r["justification"]

            # Strategy Title
            story.append(Paragraph(f"Strategy: {strategy}", styles["StrategyTitle"]))

            # Justification Content
            story.append(Paragraph("<b>Justification:</b>", styles["Justification"]))

            if isinstance(justification_content, list):
                # If justification is already a list of points (ideal for your goal)
                list_items = [
                    Paragraph(point, styles["BulletPoint"])
                    for point in justification_content
                ]
                story.append(
                    ListFlowable(
                        list_items,
                        bulletAnchor="middle",
                        bulletkind="bullet",
                        leftIndent=0.25 * inch,
                        spaceAfter=15,
                    )
                )
            else:
                # Fallback: If justification is still a single string (as in your current JSON output)
                # We will try to split it heuristically (e.g., by sentences)
                # NOTE: A better approach is to change the LLM output, but this is a fallback.

                # Simple heuristic split (e.g., splitting by sentence or based on source data structure)
                # If your LLM output always puts points with a newline, you can split by '\n'
                points = justification_content.split("\n")

                # Clean up empty lines and create bullet points
                cleaned_points = [p.strip() for p in points if p.strip()]

                list_items = [
                    Paragraph(point, styles["BulletPoint"]) for point in cleaned_points
                ]

                # Only add the ListFlowable if there are points
                if list_items:
                    story.append(
                        ListFlowable(
                            list_items,
                            bulletAnchor="middle",
                            leftIndent=0.25 * inch,
                            spaceAfter=15,
                        )
                    )
                else:
                    # If splitting failed or was a single point, render as a regular paragraph
                    story.append(
                        Paragraph(justification_content, styles["Justification"])
                    )

            # Optional: Add a small space between items
            story.append(Spacer(1, 0.1 * inch))

        # Build the PDF document from the story
        doc.build(story)

        # The pdf_buffer now contains the properly structured PDF data

        # 3. Create the ADK Artifact (`Part` object)
        artifact = Part(
            inline_data=Blob(
                # Use the correct MIME type for PDF
                mime_type="application/pdf",
                data=pdf_buffer.getvalue(),
            )
        )

        # 4. Save the Artifact using ToolContext
        # Note: tool_context.save_artifact is an async call in some ADK versions,
        # but for simplicity in a sync tool function, we'll assume it's synchronous
        # or the framework handles it.
        filename = f"{client_name.replace(' ', '_')}_Strategy_Report.pdf"
        version = tool_context.save_artifact(filename=filename, artifact=artifact)

        # --- Upload to GCS ---
        storage_client = _get_gcs_client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(filename)
        # Ensure you reset the buffer's cursor before uploading again if you were reading from it
        pdf_buffer.seek(0)
        blob.upload_from_string(pdf_buffer.getvalue(), content_type="application/pdf")

        public_url = f"https://storage.googleapis.com/{bucket_name}/{filename}"
        logger.info(f"Uploaded '{filename}' to public GCS bucket.")

        tool_context.state["report_generated"] = True

        tool_context.state["final_report_url"] = public_url

        tool_context.state["client_name"] = client_name

        return f"Successfully created the Strategy Recommendation Report. It is publicly accessible at: {public_url}"

    except json.JSONDecodeError:
        return "ERROR: Agent output was not valid JSON. Could not generate PDF."
    except Exception as e:
        return f"ERROR: Failed to generate or save PDF: {e}"


generate_and_save_pdf_tool = FunctionTool(func=generate_and_save_pdf)
