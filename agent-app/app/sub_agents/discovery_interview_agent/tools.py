# tools.py

import logging
import os
import tempfile

from google.adk.agents import Agent
from google.adk.tools import FunctionTool, google_search
from google.adk.tools.agent_tool import AgentTool
from google.cloud import storage

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def _get_gcs_client():
    """Initializes and returns a Google Cloud Storage client."""
    return storage.Client()


# --- Tool 1: Final Summary PDF Generation ---


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
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

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

create_final_summary_pdf_tool = FunctionTool(func=create_final_summary_pdf)
google_search_tool = AgentTool(agent=search_agent)
