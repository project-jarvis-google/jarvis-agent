# tool.py
import os
import logging
import datetime
import re
import io
import csv
import tempfile  # Added for the new function

from google.adk.tools import FunctionTool
from google.cloud import storage

# --- ReportLab Imports ---
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- NEW: Helper function from Agent 1 ---
def _get_gcs_client():
    """Initializes and returns a Google Cloud Storage client."""
    return storage.Client()


def _convert_markdown_to_flowables(markdown_text: str):
    """
    Converts a markdown string into a list of ReportLab Flowable objects.
    Handles headers, bold, italics, and lists.
    """
    story = []
    styles = getSampleStyleSheet()

    # Add some basic styling for readability
    styles["h1"].fontSize = 18
    styles["h1"].leading = 22
    styles["h2"].fontSize = 14
    styles["h2"].leading = 18
    styles["BodyText"].leading = 14
    styles["BodyText"].spaceAfter = 6

    # Helper to convert markdown bold/italic to reportlab's <b>/<i> tags
    def format_text(text):
        text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
        # Regex to handle italics without accidentally matching list asterisks
        text = re.sub(r"(?<!\*)\*([^\*]+)\*(?!\*)", r"<i>\1</i>", text)
        return text

    lines = markdown_text.split("\n")
    for line in lines:
        stripped_line = line.strip()

        if not stripped_line:
            continue

        if stripped_line.startswith("# "):
            story.append(Paragraph(format_text(stripped_line[2:]), styles["h1"]))
            story.append(Spacer(1, 0.2 * inch))
        elif stripped_line.startswith("## "):
            story.append(Paragraph(format_text(stripped_line[2:]), styles["h2"]))
            story.append(Spacer(1, 0.1 * inch))
        elif stripped_line.startswith("### "):
            story.append(Paragraph(format_text(stripped_line[2:]), styles["h3"]))
            story.append(Spacer(1, 0.1 * inch))
        elif stripped_line.startswith(("* ", "- ")):
            p = Paragraph(f"• {format_text(stripped_line[2:])}", styles["BodyText"])
            p.style.leftIndent = 20
            story.append(p)
        elif re.match(r"^\d+\.\s", stripped_line):
            p = Paragraph(format_text(stripped_line), styles["BodyText"])
            p.style.leftIndent = 20
            story.append(p)
        elif stripped_line == "---":
            story.append(Spacer(1, 0.25 * inch))
        else:
            story.append(Paragraph(format_text(line), styles["BodyText"]))

    return story


# --- MODIFIED FUNCTION ---
def _create_gcs_file_and_get_link(report_markdown: str) -> str:
    """Generates a PDF from markdown, uploads to GCS, and returns a public URL."""

    bucket_name = os.getenv("GCS_BUCKET_NAME")
    if not bucket_name:
        return "Error: GCS_BUCKET_NAME environment variable is not set."
    if not report_markdown or len(report_markdown.strip()) < 50:
        return "Error: Tool was called with empty or invalid report text."

    try:
        storage_client = _get_gcs_client()
        bucket = storage_client.bucket(bucket_name)
    except Exception as e:
        return f"Error: Failed to connect to GCS. Check credentials. Details: {e}"

    try:
        app_name_match = re.search(
            r"Application:\s*\*\*(.*?)\*\*", report_markdown, re.IGNORECASE
        )
        if not app_name_match:
            app_name_match = re.search(
                r"Report\s*-\s*(.*)", report_markdown, re.IGNORECASE
            )

        app_name_str = app_name_match.group(1).strip() if app_name_match else "Report"
        safe_app_name = re.sub(r"[^a-zA-Z0-9_-]", "", app_name_str.replace(" ", "_"))
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        pdf_blob_name = f"compliance-reports/{safe_app_name}_{timestamp}.pdf"

        # Using a temporary file for consistency with Agent 1
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            doc = SimpleDocTemplate(tmp.name, pagesize=letter)
            story = _convert_markdown_to_flowables(report_markdown)
            doc.build(story)
            tmp_path = tmp.name

        pdf_blob = bucket.blob(pdf_blob_name)
        pdf_blob.upload_from_filename(tmp_path, content_type="application/pdf")
        os.remove(tmp_path)

        # --- MODIFICATION START: Changed link generation ---
        # Replaced the signed URL with a direct public URL, like in Agent 1.
        public_url = f"https://storage.googleapis.com/{bucket_name}/{pdf_blob_name}"
        logger.info(f"Uploaded '{pdf_blob_name}' to public GCS bucket.")
        return f"Successfully created the compliance report. It is publicly accessible at: {public_url}"
        # --- MODIFICATION END ---

    except Exception as e:
        logger.error(f"Failed to generate or upload report: {e}", exc_info=True)
        return (
            f"Error: An unexpected error occurred during PDF generation. Details: {e}"
        )


# --- NEW FUNCTION: To match the CSV processing pattern of Agent 1 ---
def process_and_upload_csv(filename: str, file_content: str) -> str:
    """
    Reads CSV content from a string, adds a processing date column, uploads the
    updated CSV to GCS, and returns a public URL.

    Args:
        filename: The name of the file being processed.
        file_content: The string content of the uploaded file.

    Returns:
        A string containing the public URL of the processed CSV file or an error message.
    """
    bucket_name = os.getenv("GCS_BUCKET_NAME", "jarvis-agent")
    if not bucket_name:
        return "Error: GCS_BUCKET_NAME environment variable is not set."

    logger.info(f"Received request to process and re-upload file '{filename}'.")
    try:
        # 1. Read the CSV from the input string
        reader = csv.reader(io.StringIO(file_content))
        data = list(reader)

        # 2. Add new data (example: adding a processing date)
        if data:
            data[0].append("ProcessedDate")  # Add header
            processing_date = str(datetime.date.today())
            for row in data[1:]:  # Skip header row
                row.append(processing_date)

        # 3. Write modified data to a new in-memory CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerows(data)
        updated_csv_content = output.getvalue().encode("utf-8")

        # 4. Upload the new CSV to GCS
        base_filename = os.path.splitext(filename)[0]
        processed_filename = f"{base_filename}_processed.csv"
        gcs_path = f"processed-csvs/{processed_filename}"

        storage_client = _get_gcs_client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(gcs_path)
        blob.upload_from_string(updated_csv_content, content_type="text/csv")

        # 5. Return the public URL, just like in Agent 1
        public_url = f"https://storage.googleapis.com/{bucket_name}/{gcs_path}"
        logger.info(f"Successfully uploaded processed CSV to {public_url}")
        return f"The file has been processed. The updated CSV is publicly accessible at: {public_url}"

    except Exception as e:
        logger.error(f"Error processing and uploading CSV file: {e}", exc_info=True)
        return f"Error: Could not process or upload the file. Error: {e}"


# --- Tool Definitions ---
# Your original csv_reader_tool is now replaced by the more capable process_and_upload_csv
create_gcs_file_tool = FunctionTool(_create_gcs_file_and_get_link)
process_and_upload_csv_tool = FunctionTool(process_and_upload_csv)
