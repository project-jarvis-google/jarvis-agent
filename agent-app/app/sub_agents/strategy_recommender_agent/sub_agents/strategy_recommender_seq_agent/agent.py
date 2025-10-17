from google.adk.agents import SequentialAgent

# from google.adk.artifacts import GcsArtifactService
from google.adk.artifacts import InMemoryArtifactService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from .sub_agents.parallel_reports_analyzer_agent import parallel_reports_analyzer_agent
from .sub_agents.report_generation_agent import strategy_report_generator_agent
from .sub_agents.source_reports_staging_agent import source_reports_staging_agent

MODEL = "gemini-2.5-flash"

strategy_recommender_seq_agent = SequentialAgent(
    name="strategy_recommender_seq_agent",
    description=(
        """Executes a sequence of source reports staging, then parallel reports analysis and finally report generation"""
    ),
    sub_agents=[
        source_reports_staging_agent,
        parallel_reports_analyzer_agent,
        strategy_report_generator_agent,
    ],
)


# Instantiate the desired artifact service
artifact_service = InMemoryArtifactService()

session_service = InMemorySessionService()

runner = Runner(
    agent=strategy_recommender_seq_agent,
    app_name="strategy_recommender_seq_agent",
    session_service=session_service,
    artifact_service=artifact_service,  # Provide the service instance here
)
