from google.cloud import storage
import os
from markdown_it import MarkdownIt
from xhtml2pdf import pisa 
import io
import json
import logging
import datetime

# --- Logging Configuration ---
# Configure the logging module to output messages with a timestamp, log level, and the message itself.
# This setup directs log output to the console.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# --- Environment Variables ---
BUCKET_NAME = os.environ.get("BUCKET_NAME", "agent-cloud-service-recomendation")


def download_pdf_from_gcs(file_name: str, expiration_time: int = 24):
    try:
        
        logging.info(f"Initializing GCS client to download '{file_name}'.")
        storage_client = storage.Client()

        # Get the bucket and blob (file)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(file_name)

        # Download the file to the specified local path
        logging.info(f"Starting download of '{file_name}' from bucket '{BUCKET_NAME}' with expiration time '{expiration_time}'.")
        file_name += ".pdf"
        
        expiration_time = datetime.timedelta(hours=expiration_time)

        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=expiration_time,
            method="GET",
        )

        logging.info(f"Successfully generated signed url for '{file_name}' from bucket '{BUCKET_NAME}'.")
        return signed_url

    except Exception as e:
        # Log the exception with traceback information for better debugging
        logging.error(f"Failed to generate signed '{file_name} because {e}.", exc_info=True)

async def save_generated_report_py(text: str):
    """
    Converts a Markdown string to a PDF and uploads it to Google Cloud Storage.

    Args:
        text (str): A JSON string containing 'result' (Markdown text) and 'fileName'.
    """
    try:
        logging.info("Parsing JSON input.")
        data_dict = json.loads(text)
        data = data_dict['result']
        destination_blob_name = data_dict['fileName']
    except json.JSONDecodeError as e:
        logging.error("Failed to parse input JSON string.", exc_info=True)
        return
    except KeyError as e:
        logging.error(f"Missing expected key in JSON: {e}", exc_info=True)
        return

    logging.info("Converting Markdown to HTML.")
    md_parser = MarkdownIt()
    html_body = md_parser.render(data)
    
    # Complete HTML document structure with basic styling
    html_full = f"""
    <html>
      <head>
        <style>
          body {{ font-family: sans-serif; line-height: 1.6; }}
          h1, h2, h3 {{ color: #333; }}
          h1 {{ border-bottom: 2px solid #eee; padding-bottom: 10px; }}
          h2 {{ border-bottom: 1px solid #eee; padding-bottom: 5px; }}
          code {{ background-color: #f4f4f4; padding: 2px 4px; border-radius: 4px; }}
          strong {{ color: #0056b3; }}
        </style>
      </head>
      <body>
        {html_body}
      </body>
    </html>
    """

    # Convert HTML string to a PDF in memory
    logging.info("Creating PDF from HTML in memory.")
    pdf_stream = io.BytesIO()
    pisa_status = pisa.CreatePDF(
        io.StringIO(html_full),
        dest=pdf_stream
    )

    # Exit if the PDF creation failed
    if pisa_status.err:
        logging.error(f"Error creating PDF with xhtml2pdf: {pisa_status.err}")
        return

    logging.info("PDF created successfully in memory.")

    # Upload the in-memory PDF to GCS
    try:
        logging.info(f"Initializing GCS client for upload to bucket '{BUCKET_NAME}'.")
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        
        # if not destination_blob_name[:-3] != ".":
        #     destination_blob_name += ".pdf"
            
        blob = bucket.blob(destination_blob_name)

        # Reset the stream's position to the beginning before uploading
        pdf_stream.seek(0)

        logging.info(f"Uploading '{destination_blob_name}' to GCS.")
        blob.upload_from_file(pdf_stream, content_type='application/pdf')

        logging.info(f"Successfully uploaded '{destination_blob_name}' to bucket '{BUCKET_NAME}'.")
        # Note: blob.public_url is only accessible if the object is publicly shared.
        logging.info(f"Public URL (if bucket is public): {blob.public_url}")

    except Exception as e:
        logging.error(f"An error occurred during GCS upload for '{destination_blob_name}'.", exc_info=True)
    finally:
        # Ensure the stream is closed
        pdf_stream.close()