"""Business Logic Extraction Agent: Analyzes legacy code to identify and extract
business rules into human-readable documentation."""

from google.adk.agents import LlmAgent

from .prompt import BUSINESS_LOGIC_EXTRACTION_PROMPT
from .sub_agents.business_logic_seq_agent.agent import business_logic_seq_agent

MODEL = "gemini-2.5-flash"

business_logic_extraction_agent = LlmAgent(
    name="business_logic_extraction_agent",
    model=MODEL,
    description=(
        """Analyzes legacy Java, C#, and SQL codebases to extract business logic,
        identify complexity hotspots, and generate human-readable rule catalogs.
        Answers questions about the analyzed code."""
    ),
    instruction=BUSINESS_LOGIC_EXTRACTION_PROMPT,
    sub_agents=[business_logic_seq_agent],
    tools=[],
)
