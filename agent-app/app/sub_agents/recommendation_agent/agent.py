from google.adk.agents import LlmAgent

# from .writer import save_generated_report_py
from google.adk.artifacts import GcsArtifactService  # InMemoryArtifactService
from google.adk.tools import FunctionTool

from ...utils.download import download_pdf_from_gcs, save_generated_report_py
from .config import MODEL
from .prompt import RECCM_AGENT_PROMPT

artifactService = GcsArtifactService(bucket_name="your-gcs-bucket-for-adk-artifacts")

recommendation_agent = LlmAgent(
    name="Cloud_Service_Advisor_AI_Agent",
    model=MODEL,
    description=("Answers user's query about service recommendation."),
    instruction=RECCM_AGENT_PROMPT,
    # after_agent_callback=save_generated_report_py
    tools=[
        FunctionTool(func=save_generated_report_py),
        FunctionTool(func=download_pdf_from_gcs),
    ],
)
