from google.adk.agents import LlmAgent

from .database_identification_tools import identify_databases
from .prompt import DATABASE_ANALYZER_PROMPT

MODEL = "gemini-2.5-pro"

database_analyzer_agent = LlmAgent(
    name="database_analyzer_agent",
    model=MODEL,
    description=(
        """
            Agent for analyzing the source code and configuration files
            and list all the database being used.
        """
    ),
    instruction=DATABASE_ANALYZER_PROMPT,
    tools=[identify_databases],
    disallow_transfer_to_parent=True
)