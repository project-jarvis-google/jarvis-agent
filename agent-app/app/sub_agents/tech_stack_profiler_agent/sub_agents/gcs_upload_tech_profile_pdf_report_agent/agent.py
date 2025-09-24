import os
import tempfile

from datetime import datetime
from fpdf import FPDF
from google.cloud import storage
from google.adk.agents import LlmAgent
from google.adk.tools import ToolContext

MODEL = "gemini-2.5-flash"  

# def upload_report_to_gcs_as_pdf(generated_report: str, tool_context: ToolContext) -> str:
def upload_report_to_gcs_as_pdf(tool_context: ToolContext) -> str:
    
    bucket_name = os.getenv("GCS_BUCKET_NAME_TECH_PROFILE")
    if not bucket_name:
        return "Error: GCS_BUCKET_NAME is not configured."
    # bucket_name = "GCS_BUCKET_NAME_TECH_PROFILE"

    filename = "TechProfile/" + datetime.now().strftime("%d%m%Y%H%M%S") + "-tech-profile" + ".pdf"

    generated_report = tool_context.state["generated_report"]
    print("generated_report => ", generated_report)

    pdf = FPDF()
    pdf.add_page()
    for x in generated_report.splitlines():
        if("###" in x):
            pdf.set_font("Arial", style="B", size = 15)
            x = x.replace("###","").strip()
        elif("##" in x):
            pdf.set_font("Arial", style="B", size = 17)
            x = x.replace("##","").strip()
        else:
            pdf.set_font("Arial", size = 13)
        pdf.cell(200, 10, txt = x, ln = 1, align = 'L')

    custom_temp_path = os.getenv("CUSTOM_TEMP_PATH")
    # custom_temp_path="/usr/local/google/home/cbangera/Projects/Jarvis/jarvis-agent/local-temp-dir"

    # with tempfile.TemporaryDirectory(dir=custom_temp_path, delete=False) as tmpdirname:
    with tempfile.TemporaryDirectory(dir=custom_temp_path) as tmpdirname:
        # print(f'Temporary directory created at: {tmpdirname}')
        pdf.output(tmpdirname + "/temp.pdf")

        print(f'File created at: {tmpdirname}')
        
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(filename)
        blob.upload_from_filename(tmpdirname + "/temp.pdf", content_type='application/pdf')

    public_url = f"https://storage.googleapis.com/{bucket_name}/{filename}" 
    print(f"Uploaded '{filename}' to public GCS bucket.")
    return f"Successfully created the questionnaire. It is publicly accessible at: {public_url}"

gcs_upload_tech_profile_pdf_report_agent = LlmAgent(
    name="gcs_upload_tech_profile_pdf_report_agent",
    description=(
        """Generates a pdf report from the existing report string stored in the tool context and uploads it 
        to the GCS bucket"""
    ),
    tools=[upload_report_to_gcs_as_pdf]
)

# if __name__ == '__main__':
#     upload_report_to_gcs_as_pdf("""
# ## Summary of Tech Profiling:

# ### Programming Language Identification and Breakdown:
# +--------+-------+
# | item   |   qty |
# +========+=======+
# | spam   |    42 |
# +--------+-------+
# | eggs   |   451 |
# +--------+-------+
# | bacon  |     0 |
# +--------+-------+
# """, None)








"""
## Summary of Tech Profiling:

### Source Code Directory Location:
/usr/local/google/home/cbangera/Projects/Jarvis/jarvis-agent/local-temp-dir/tmphb0gghyk

### Programming Language Identification and Breakdown:
language       percentage
Java           99.89%
Dockerfile     0.11%

### Framework Identification and Categorization:
name           category
Spring Boot    Web Framework
Spring Cloud   Cloud Framework
Eureka         Service Discovery
Resilience4j   Fault Tolerance
Micrometer     Monitoring
Lombok         Utility
Maven          Build Tool

### Database Identification:
name           configurations
H2 Database    in-memory
"""