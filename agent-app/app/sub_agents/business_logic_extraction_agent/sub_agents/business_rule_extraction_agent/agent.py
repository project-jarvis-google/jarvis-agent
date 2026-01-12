from google.adk.agents import LlmAgent

from .prompt import BUSINESS_RULE_EXTRACTION_PROMPT
from .rule_extraction_tools import read_target_files

MODEL = "gemini-2.5-flash"

business_rule_extraction_agent = LlmAgent(
    name="business_rule_extraction_agent",
    model=MODEL,
    description=(
        """
            Agent for extracting business rules from source code.
            Translates logic into IF-THEN format and links to source lines.
        """
    ),
    instruction=BUSINESS_RULE_EXTRACTION_PROMPT,
    tools=[read_target_files],
)