"""Business Logic Extraction Agent: Analyzes legacy code to identify and extract
business rules into human-readable documentation."""

from google.adk.agents import LlmAgent

from .prompt import BUSINESS_LOGIC_EXTRACTION_PROMPT

# Note: You will need to create these sub-agents based on the epic requirements.
# from .sub_agents.code_ingestion_agent import code_ingestion_agent
# from .sub_agents.static_analysis_agent import static_analysis_agent
# from .sub_agents.rule_extraction_agent import rule_extraction_agent
# from .sub_agents.reporting_agent import reporting_agent

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
    # sub_agents=[code_ingestion_agent, static_analysis_agent, rule_extraction_agent, reporting_agent],
)
