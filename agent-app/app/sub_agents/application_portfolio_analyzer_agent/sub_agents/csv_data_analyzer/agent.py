from google.adk.agents import LlmAgent

from .prompt import APPLICATION_PORTFOLIO_CSV_DATA_ANALYZER_PROMPT

MODEL = "gemini-2.5-flash"

csv_data_analyzer_agent = LlmAgent(
    name="csv_data_analyzer_agent",
    model=MODEL,
    description=(
        """ 
        Analyzes the data inside the application portfolio csv file and provides useful insights.
    """
    ),
    instruction=APPLICATION_PORTFOLIO_CSV_DATA_ANALYZER_PROMPT,
    # output_key="application_portfolio_analyzer_output",
)

# artifact_service = InMemoryArtifactService()
# session_service = InMemorySessionService()

# runner = Runner(
#     agent=csv_data_analyzer_agent,
#     app_name="csv_data_analyzer_agent",
#     session_service=session_service,
#     artifact_service=artifact_service # Provide the service instance here
# )
