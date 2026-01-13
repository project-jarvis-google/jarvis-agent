from google.adk.agents import LlmAgent

from .prompt import BUSINESS_RULE_EXTRACTION_PROMPT
from .rule_extraction_tools import ask_gemini

MODEL = "gemini-2.5-pro"

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
    tools=[ask_gemini],
)