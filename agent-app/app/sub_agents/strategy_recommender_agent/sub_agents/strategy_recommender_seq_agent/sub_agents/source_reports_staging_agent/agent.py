from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.artifacts import InMemoryArtifactService
from google.adk.sessions import InMemorySessionService
from .report_upload_tool import save_generated_report_tool, extract_sections_tool
from .halt_tool import halt_workflow_tool
from .prompt import SOURCE_REPORTS_STAGING_PROMPT

MODEL = "gemini-2.5-flash"

source_reports_staging_agent = LlmAgent(
    name="source_reports_staging_agent",
    model=MODEL,
    description=(
        "Agent for creating a temporary storage,extracting the summary from the input Discovert Report for source reports analysis"
    ),
    instruction=SOURCE_REPORTS_STAGING_PROMPT,
    tools=[save_generated_report_tool, extract_sections_tool, halt_workflow_tool],
)

# Instantiate the desired artifact service
artifact_service = InMemoryArtifactService()
session_service = InMemorySessionService()

runner = Runner(
    agent=source_reports_staging_agent,
    app_name="source_reports_staging_app",
    session_service=session_service,
    artifact_service=artifact_service,  # Provide the service instance here
)
