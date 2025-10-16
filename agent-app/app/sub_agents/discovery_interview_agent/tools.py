# tools.py
import os
import logging
import datetime
import tempfile
import csv
import io
from google.adk.tools import FunctionTool, google_search
from google.adk.tools.agent_tool import AgentTool
from google.cloud import storage
from google.adk.agents import Agent

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def _get_gcs_client():
    """Initializes and returns a Google Cloud Storage client."""
    return storage.Client()


# --- Tool 1: Questionnaire Generation ---


def compile_questions_to_sheet(
    client_name: str, topic: str, questions: list[str]
) -> str:
    """
    Creates a CSV file with discovery questions, uploads it to a GCS bucket,
    and returns a public URL for the file.

    Args:
        client_name: The name of the client for whom the questionnaire is being created.
        topic: The main discovery topic (e.g., "database modernization").
        questions: A list of question strings to include in the CSV.

    Returns:
        A string containing the public URL of the generated CSV file or an error message.
    """

    bucket_name = os.getenv("GCS_BUCKET_NAME")
    if not bucket_name:
        return "Error: GCS_BUCKET_NAME is not configured."

    try:
        filename = f"Questionarre/Questionnaire-{client_name}-{topic}.csv"

        # Use a temporary file to build the CSV
        with tempfile.NamedTemporaryFile(
            mode="w+", delete=False, suffix=".csv", newline="", encoding="utf-8"
        ) as tmp:
            writer = csv.writer(tmp)
            writer.writerow(["Discovery Questions"])
            writer.writerow(["Generated on:", str(datetime.date.today())])
            writer.writerow([])
            writer.writerow(["Question", "Answer"])
            for q in questions:
                writer.writerow([q, ""])
            tmp_path = tmp.name

        # Upload to GCS
        storage_client = _get_gcs_client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(filename)
        blob.upload_from_filename(tmp_path, content_type="text/csv")

        os.remove(tmp_path)

        public_url = f"https://storage.googleapis.com/{bucket_name}/{filename}"

        logger.info(f"Uploaded '{filename}' to public GCS bucket.")
        return f"Successfully created the questionnaire. It is publicly accessible at: {public_url}"

    except Exception as e:
        logger.error(f"Error creating or uploading CSV file: {e}", exc_info=True)
        return f"Error: Could not create or upload the questionnaire. Error: {e}"


# --- Tool 2: Analyze and Update Sheet ---


def read_and_update_sheet_from_attachment(
    filename: str,
    file_content: str,  # The agent passes the file's content as a string
    analysis_data: list[dict],
) -> str:
    """
    Reads a  string of a CSV file, adds analysis columns, uploads the
    updated CSV to GCS, and returns a public URL.

    Args:
        filename: The name of the file being analyzed.
        file_content: The  string content of the uploaded file.
        analysis_data: A list of dictionaries with analysis ('classification', 'tags', 'row').

    Returns:
        A string containing the public URL of the analyzed CSV file or an error message.
    """
    bucket_name = os.getenv("GCS_BUCKET_NAME")
    if not bucket_name:
        return "Error: GCS_BUCKET_NAME is not configured."

    logger.info(f"Received direct request to process file '{filename}'.")
    try:
        reader = csv.reader(io.StringIO(file_content))
        data = list(reader)
        # 3. Add Analysis Data in Memory
        if data:
            data[0].extend(["Category", "Tag"])
            for item in analysis_data:
                row_index = item["row"] - 1
                if 0 <= row_index < len(data):
                    data[row_index].extend(
                        [item.get("classification", "N/A"), item.get("tags", "N/A")]
                    )

        # 4. Write Modified Data to a New CSV in Memory
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerows(data)
        updated_csv_content = output.getvalue().encode("utf-8")
        # 5. Upload Updated CSV to GCS
        # First, get the base name of the file without its extension.
        base_filename = os.path.splitext(filename)[0]
        analyzed_filename = f"{base_filename}_analyzed.csv"
        gcs_path = f"Analysis/{analyzed_filename}"

        storage_client = _get_gcs_client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(gcs_path)
        blob.upload_from_string(updated_csv_content, content_type="text/csv")

        # 6. Return Public URL
        public_url = f"https://storage.googleapis.com/{bucket_name}/{gcs_path}"
        logger.info(f"Successfully uploaded analyzed CSV to {public_url}")
        return f"The analysis is complete. The updated CSV is publicly accessible at: {public_url}"
    except Exception as e:
        logger.error(f"Error processing and uploading CSV file: {e}", exc_info=True)
        return f"Error: Could not analyze or upload the file. Error: {e}"


# --- Tool 3: Final Summary PDF Generation ---


def create_final_summary_pdf(
    client_name: str,
    topic: str,
    interview_date: str,
    attendees: str,
    executive_summary: str,
    pain_points: list[str],
    desired_outcomes: list[str],
    gcp_solutions: list[str],
) -> str:
    """
    Creates a formatted PDF summary document, uploads it to GCS, and returns a public URL.

    Args:
        client_name: The name of the client.
        topic: The main discovery topic.
        interview_date: The date of the discovery interview.
        attendees: A list or string of attendees.
        executive_summary: The generated executive summary text.
        pain_points: A list of strings describing identified pain points.
        desired_outcomes: A list of strings describing desired business outcomes.
        gcp_solutions: A list of strings of recommended GCP solutions.

    Returns:
        A string containing the public URL of the generated PDF file or an error message.
    """
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch

    bucket_name = os.getenv("GCS_BUCKET_NAME")
    if not bucket_name:
        return "Error: GCS_BUCKET_NAME is not configured."

    try:
        filename = f"Summary/Discovery Summary-{client_name}-{topic}.pdf"

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            doc = SimpleDocTemplate(tmp.name)
            styles = getSampleStyleSheet()
            story = []

            # --- Build the PDF Content ---
            story.append(Paragraph(f"Discovery Summary: {client_name}", styles["h1"]))
            story.append(Spacer(1, 0.2 * inch))
            story.append(Paragraph("Client and Interview Details", styles["h2"]))
            story.append(Paragraph(f"<b>Client:</b> {client_name}", styles["BodyText"]))
            story.append(
                Paragraph(f"<b>Date:</b> {interview_date}", styles["BodyText"])
            )
            story.append(
                Paragraph(f"<b>Attendees:</b> {attendees}", styles["BodyText"])
            )
            story.append(Spacer(1, 0.2 * inch))

            story.append(Paragraph("Executive Summary", styles["h2"]))
            story.append(Paragraph(executive_summary, styles["BodyText"]))
            story.append(Spacer(1, 0.2 * inch))

            story.append(Paragraph("Identified Pain Points", styles["h2"]))
            for pp in pain_points:
                story.append(Paragraph(f"• {pp}", styles["Bullet"]))
            story.append(Spacer(1, 0.2 * inch))

            story.append(Paragraph("Desired Business Outcomes", styles["h2"]))
            for out in desired_outcomes:
                story.append(Paragraph(f"• {out}", styles["Bullet"]))
            story.append(Spacer(1, 0.2 * inch))

            story.append(Paragraph("Referenced GCP Solutions", styles["h2"]))
            for solution in gcp_solutions:
                story.append(Paragraph(f"• {solution}", styles["Bullet"]))

            doc.build(story)
            tmp_path = tmp.name

        # --- Upload to GCS ---
        storage_client = _get_gcs_client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(filename)
        blob.upload_from_filename(tmp_path, content_type="application/pdf")

        os.remove(tmp_path)

        public_url = f"https://storage.googleapis.com/{bucket_name}/{filename}"
        logger.info(f"Uploaded '{filename}' to public GCS bucket.")
        return f"Successfully created the final summary PDF. It is publicly accessible at: {public_url}"

    except Exception as e:
        logger.error(f"Error creating or uploading PDF document: {e}", exc_info=True)
        return f"Error: Could not create or upload the summary PDF. Error: {e}"


# --- Tool Registration ---
search_agent = Agent(
    model="gemini-2.0-flash",
    name="SearchAgent",
    instruction="You're a specialist in Google Search",
    tools=[google_search],
)
compile_questions_to_sheet_tool = FunctionTool(func=compile_questions_to_sheet)
read_and_update_sheet_tool = FunctionTool(func=read_and_update_sheet_from_attachment)
create_final_summary_pdf_tool = FunctionTool(func=create_final_summary_pdf)
google_search_tool = AgentTool(agent=search_agent)
