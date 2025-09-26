import tempfile

from fpdf import FPDF
from google.cloud import storage

def convert_str_to_pdf(
        data_str: str,
        format: str,
        custom_temp_path: str = None,
        del_pdf_temp_file_after_creation: bool = True,
        upload_pdf_to_gcs: bool = True,
        gcs_bucket_name: str = None,
        gcs_file_name: str = None
    ) -> dict:

    result = {
        "temp_file_location": None,
        "is_gcs_file_upload_successful": False
    }
    
    pdf = FPDF()
    pdf.add_page()

    match format:
        case "markdown":
            markdown_str_to_pdf_str(data_str)

    with tempfile.TemporaryDirectory(dir=custom_temp_path, delete=del_pdf_temp_file_after_creation) as tmpdirname:
        # print(f'Temporary directory created at: {tmpdirname}')
        pdf.output(tmpdirname + "/temp.pdf")

        print(f'File created at: {tmpdirname}')

        if(not del_pdf_temp_file_after_creation):
            result["temp_file_location"] = tmpdirname + "/temp.pdf"
            
        if (upload_pdf_to_gcs):
            storage_client = storage.Client()
            bucket = storage_client.bucket(gcs_bucket_name)
            blob = bucket.blob(gcs_file_name)
            blob.upload_from_filename(tmpdirname + "/temp.pdf", content_type='application/pdf')
            result["gcs_file_upload_successful"] = True

    return result

def markdown_str_to_pdf_str(data_str: str, pdf: FPDF):
    for x in data_str.splitlines():
        if("###" in x):
            pdf.set_font("Arial", style="B", size = 15)
            x = x.replace("###","").strip()
        elif("##" in x):
            pdf.set_font("Arial", style="B", size = 17)
            x = x.replace("##","").strip()
        else:
            pdf.set_font("Arial", size = 13)
        pdf.cell(200, 10, txt = x, ln = 1, align = 'L')