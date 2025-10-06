import os
import logging
import datetime
import re
import io
import csv
from google.adk.tools import FunctionTool
from google.cloud import storage

# --- ReportLab Imports ---
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _convert_markdown_to_flowables(markdown_text: str):
    """
    Converts a markdown string into a list of ReportLab Flowable objects.
    Handles headers, bold, italics, and lists.
    """
    story = []
    styles = getSampleStyleSheet()

    # Add some basic styling for readability
    styles['h1'].fontSize = 18
    styles['h1'].leading = 22
    styles['h2'].fontSize = 14
    styles['h2'].leading = 18
    styles['BodyText'].leading = 14
    styles['BodyText'].spaceAfter = 6

    # Helper to convert markdown bold/italic to reportlab's <b>/<i> tags
    def format_text(text):
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        # Regex to handle italics without accidentally matching list asterisks
        text = re.sub(r'(?<!\*)\*([^\*]+)\*(?!\*)', r'<i>\1</i>', text)
        return text

    lines = markdown_text.split('\n')
    for line in lines:
        stripped_line = line.strip()

        if not stripped_line:
            continue  # Skip blank lines in the story

        if stripped_line.startswith('# '):
            story.append(Paragraph(format_text(stripped_line[2:]), styles['h1']))
            story.append(Spacer(1, 0.2 * inch))
        elif stripped_line.startswith('## '):
            story.append(Paragraph(format_text(stripped_line[2:]), styles['h2']))
            story.append(Spacer(1, 0.1 * inch))
        elif stripped_line.startswith('### '):
            story.append(Paragraph(format_text(stripped_line[2:]), styles['h3']))
            story.append(Spacer(1, 0.1 * inch))
        elif stripped_line.startswith(('* ', '- ')):
            # Create a Paragraph with a bullet character and indent it
            p = Paragraph(f"• {format_text(stripped_line[2:])}", styles['BodyText'])
            p.style.leftIndent = 20
            story.append(p)
        elif re.match(r'^\d+\.\s', stripped_line):
            # Handle numbered lists and indent them
            p = Paragraph(format_text(stripped_line), styles['BodyText'])
            p.style.leftIndent = 20
            story.append(p)
        elif stripped_line == '---':
            story.append(Spacer(1, 0.25 * inch))
        else:
            # Regular paragraph
            story.append(Paragraph(format_text(line), styles['BodyText']))

    return story


def _create_gcs_file_and_get_link(report_markdown: str) -> str:
    """Generates a PDF from markdown, uploads to GCS, and returns a signed URL that forces a download."""
    bucket_name = os.getenv("GCS_BUCKET_NAME")
    if not bucket_name:
        return "Error: GCS_BUCKET_NAME environment variable is not set."
    if not report_markdown or len(report_markdown.strip()) < 50:
        return "Error: Tool was called with empty or invalid report text."

    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
    except Exception as e:
        return f"Error: Failed to connect to GCS. Check credentials. Details: {e}"

    try:
        # Improved regex to find the application name for the PDF filename
        app_name_match = re.search(r"Application:\s*\*\*(.*?)\*\*", report_markdown, re.IGNORECASE)
        if not app_name_match:
            app_name_match = re.search(r"Report\s*-\s*(.*)", report_markdown, re.IGNORECASE)

        app_name_str = app_name_match.group(1).strip() if app_name_match else "Report"
        safe_app_name = re.sub(r'[^a-zA-Z0-9_-]', '', app_name_str.replace(" ", "_"))
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        pdf_blob_name = f"compliance-reports/{safe_app_name}_{timestamp}.pdf"

        # PDF Generation (no changes)
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, rightMargin=inch, leftMargin=inch, topMargin=inch, bottomMargin=inch)
        story = _convert_markdown_to_flowables(report_markdown)
        doc.build(story)
        pdf_bytes = pdf_buffer.getvalue()
        pdf_buffer.close()

        # GCS upload (no changes)
        pdf_blob = bucket.blob(pdf_blob_name)
        pdf_blob.upload_from_string(pdf_bytes, content_type='application/pdf')

        # Get just the filename part for the download attribute
        download_filename = pdf_blob_name.split("/")[-1]

        download_url = pdf_blob.generate_signed_url(
            version="v4",
            expiration=datetime.timedelta(minutes=15),
            method="GET",
            # This parameter tells the browser to download the file automatically
            response_disposition=f'attachment; filename="{download_filename}"'
        )
        return download_url
    except Exception as e:
        logger.error(f"Failed to generate or upload report: {e}", exc_info=True)
        return f"Error: An unexpected error occurred during PDF generation. Details: {e}"


def read_and_process_csv(file_path: str) -> str:
    """
    Reads a CSV file containing application data and formats it into a single
    string for the agent to process.
    Expected columns: AppName, AppDescription, DataType
    """
    try:
        processed_apps = []
        with open(file_path, mode='r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            for i, row in enumerate(reader):
                if not all(key in row for key in ['AppName', 'AppDescription', 'DataType']):
                    return f"Error: CSV row {i+1} is missing one of the required columns: AppName, AppDescription, DataType."
                app_string = (
                    f"--- Application {i+1} ---\n"
                    f"AppName: {row['AppName']}\n"
                    f"AppDescription: {row['AppDescription']}\n"
                    f"DataType: {row['DataType']}\n"
                )
                processed_apps.append(app_string)
        if not processed_apps:
            return "Error: The CSV file appears to be empty or in an invalid format."
        return "\n".join(processed_apps)
    except Exception as e:
        logger.error(f"Failed to process CSV file: {e}", exc_info=True)
        return f"Error: An unexpected error occurred while reading the CSV file. Details: {e}"


# --- Tool Definitions ---
create_gcs_file_tool = FunctionTool(_create_gcs_file_and_get_link)
csv_reader_tool = FunctionTool(read_and_process_csv)