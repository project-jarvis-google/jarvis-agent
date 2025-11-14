from google.adk.agents import LlmAgent

from .gemini_cli_codebase_analysis_tools import identify_technical_aspects
from .prompt import GEMINI_CLI_AGENT_PROMPT

MODEL = "gemini-2.5-pro"

gemini_cli_analyzer_agent = LlmAgent(
    name="gemini_cli_analyzer_agent",
    model=MODEL,
    description=(
        """
            Agent for analyzing the source code and listing all the technical details.
        """
    ),
    instruction=GEMINI_CLI_AGENT_PROMPT,
    tools=[identify_technical_aspects],
    disallow_transfer_to_parent=True,
)
