import os
from datetime import datetime

from google.adk.agents import LlmAgent
from google.adk.tools import ToolContext

from app.utils.pdf_converter import convert_str_to_pdf

MODEL = "gemini-2.5-flash"


# def upload_report_to_gcs_as_pdf(generated_report: str, tool_context: ToolContext) -> str:
def upload_report_to_gcs_as_pdf(tool_context: ToolContext) -> str:
    bucket_name = os.getenv("GCS_BUCKET_NAME_TECH_PROFILE")
    if not bucket_name:
        return "Error: GCS_BUCKET_NAME is not configured."
    # bucket_name = "GCS_BUCKET_NAME_TECH_PROFILE"

    filename = (
        "TechProfile/"
        + datetime.now().strftime("%d%m%Y%H%M%S")
        + "-tech-profile"
        + ".pdf"
    )

    generated_report = tool_context.state["generated_report"]
    print("generated_report => ", generated_report)

    custom_temp_path = os.getenv("CUSTOM_TEMP_PATH")
    # custom_temp_path="/usr/local/google/home/cbangera/Projects/Jarvis/jarvis-agent/local-temp-dir"

    is_gcs_upload_successful = convert_str_to_pdf(
        data_str=generated_report,
        format="markdown",
        custom_temp_path=custom_temp_path,
        del_pdf_temp_file_after_creation=True,
        upload_pdf_to_gcs=True,
        gcs_bucket_name=bucket_name,
        gcs_file_name=filename,
    ).get("is_gcs_file_upload_successful")

    if is_gcs_upload_successful:
        public_url = f"https://storage.googleapis.com/{bucket_name}/{filename}"
        print(f"Uploaded '{filename}' to public GCS bucket.")
        return f"Successfully created the pdf report. It is publicly accessible at: {public_url}"

    return "Pdf report creation unsuccessful!"


gcs_upload_tech_profile_pdf_report_agent = LlmAgent(
    name="gcs_upload_tech_profile_pdf_report_agent",
    description=(
        """Generates a pdf report from the existing report string stored in the tool context and uploads it 
        to the GCS bucket"""
    ),
    tools=[upload_report_to_gcs_as_pdf],
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
