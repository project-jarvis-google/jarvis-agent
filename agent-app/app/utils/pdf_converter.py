import logging
import tempfile

from app.utils.gcs import upload_str_to_gcs_bucket
from fpdf import FPDF

# It's good practice to have a logger instance per module.
logger = logging.getLogger(__name__)
def convert_str_to_pdf(
        data_str: str,
        format: str,
        custom_temp_path: str = None,
        del_pdf_temp_file_after_creation: bool = True,
        upload_pdf_to_gcs: bool = True,
        gcs_bucket_name: str = None,
        gcs_file_name: str = None
    ) -> dict:
    """Converts a string to a PDF file, optionally saving it and uploading to GCS.
    
    Args:
        data_str: The input string to convert.
        format: The format of the input string (e.g., "markdown").
        custom_temp_path: A custom path for temporary files.
        del_pdf_temp_file_after_creation: If True, the temporary PDF is deleted.
        upload_pdf_to_gcs: If True, uploads the PDF to Google Cloud Storage.
        gcs_bucket_name: The GCS bucket name for upload.
        gcs_file_name: The destination file name in GCS.
        
    Returns:
        A dictionary containing the operation result.
    """
    result = {
        "temp_file_location": None,
        "is_gcs_file_upload_successful": False
    }

    if upload_pdf_to_gcs and (not gcs_bucket_name or not gcs_file_name):
        logger.error("GCS bucket name and file name are required for upload.")
        return result

    try:
        pdf = FPDF()
        pdf.add_page()

        if format == "markdown":
            markdown_str_to_pdf_str(data_str, pdf)
        else:
            logger.warning(f"Unsupported format: {format}. Creating a blank PDF.")
            # Or raise ValueError(f"Unsupported format: {format}")

        # TODO: Upgrade python docker base image to version 3.12 for 'delete' keyword to work
        with tempfile.TemporaryDirectory(dir=custom_temp_path) as tmpdirname:
        # with tempfile.TemporaryDirectory(dir=custom_temp_path, delete=del_pdf_temp_file_after_creation) as tmpdirname:
            temp_pdf_path = f"{tmpdirname}/temp.pdf"
            pdf.output(temp_pdf_path)
            logger.info(f"Temporary PDF created at: {temp_pdf_path}")

            if not del_pdf_temp_file_after_creation:
                # Note: This path will be invalid after the function returns if the directory is deleted.
                # Consider handling file persistence differently if needed outside this function's scope.
                result["temp_file_location"] = temp_pdf_path

            if upload_pdf_to_gcs:
                result["is_gcs_file_upload_successful"] = upload_str_to_gcs_bucket(
                    gcs_bucket_name, gcs_file_name, temp_pdf_path, "application/pdf"
                )
    except Exception as e:
        logger.error(f"Failed to convert string to PDF: {e}", exc_info=True)
        result["error"] = str(e)

    return result

def markdown_str_to_pdf_str(data_str: str, pdf: FPDF):
    """Parses a markdown-like string and adds it to the PDF object."""
    for line in data_str.splitlines():
        if line.startswith("###"):
            pdf.set_font("Arial", style="B", size=15)
            text = line.replace("###","").strip()
        elif line.startswith("##"):
            pdf.set_font("Arial", style="B", size=17)
            text = line.replace("##","").strip()
        else:
            pdf.set_font("Arial", size=13)
            text = line
        # Using multi_cell for better handling of long lines and wrapping
        pdf.multi_cell(0, 10, txt=text, align='L')
    pdf.ln()