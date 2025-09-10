import google.genai.types as types
from google.adk.agents.callback_context import CallbackContext # Or ToolContext
from google.adk.models import LlmResponse
from google.adk.artifacts import GcsArtifactService #InMemoryArtifactService

from google.cloud import storage
from markdown_it import MarkdownIt
from xhtml2pdf import pisa 
import io
import json
import os

#artifactService = GcsArtifactService(bucket_name="your-gcs-bucket-for-adk-artifacts")

BUCKET_NAME = os.environ.get("BUCKET_NAME", "agent-cloud-service-recomendation")

async def save_generated_report_py(text: str):
    print("LLM response - ")
    print(text)
    data_dict = json.loads(text)

    data = data_dict['result']
    destination_blob_name = data_dict['fileName']
    
    md_parser = MarkdownIt()
    html_body = md_parser.render(data)
    
    md_parser = MarkdownIt()
    html_body = md_parser.render(data)
    
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

    # 2. Convert HTML string to a PDF in memory using xhtml2pdf
    # This creates the PDF and writes it to an in-memory binary stream.
    pdf_stream = io.BytesIO()
    pisa_status = pisa.CreatePDF(
        io.StringIO(html_full),  # The source HTML string
        dest=pdf_stream          # The destination stream
    )

    # Exit if the PDF creation failed
    if pisa_status.err:
        print(f"❌ Error creating PDF with xhtml2pdf: {pisa_status.err}")
        return

    print("PDF created successfully in memory.")

    # 3. Upload the in-memory PDF to GCS
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        destination_blob_name = destination_blob_name
        blob = bucket.blob(destination_blob_name)

        # Before uploading, reset the stream's position to the beginning
        pdf_stream.seek(0)

        # Upload from the stream
        blob.upload_from_file(pdf_stream, content_type='application/pdf')

        print(f"✅ Successfully uploaded '{destination_blob_name}' to bucket '{BUCKET_NAME}'.")
        print(f"Public URL (if bucket is public): {blob.public_url}")

    except Exception as e:
        print(f"❌ An error occurred during GCS upload: {e}")
