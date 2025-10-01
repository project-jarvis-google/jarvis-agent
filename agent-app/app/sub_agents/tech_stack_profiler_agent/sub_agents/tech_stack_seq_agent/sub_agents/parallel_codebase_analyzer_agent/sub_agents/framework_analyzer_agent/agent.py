from google.adk.agents import LlmAgent

from .framework_identification_tools import identify_frameworks_initiator
from .prompt import FRAMEWORK_IDENTIFICATION_AGENT_PROMPT

MODEL = "gemini-2.5-pro"

framework_analyzer_agent = LlmAgent(
    name="framework_analyzer_agent",
    model=MODEL,
    description=(
        """
            Agent for analyzing the source code and listing all the frameworks used.
        """
    ),
    instruction=FRAMEWORK_IDENTIFICATION_AGENT_PROMPT,
    tools=[identify_frameworks_initiator],
)