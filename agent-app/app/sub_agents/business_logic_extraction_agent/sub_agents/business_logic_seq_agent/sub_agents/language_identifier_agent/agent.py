from google.adk.agents import LlmAgent

from .language_identification_tools import identify_languages_from_source_code
from .prompt import LANGUAGE_IDENTIFICATION_PROMPT

MODEL = "gemini-2.5-flash"

business_logic_language_identifier_agent = LlmAgent(
    name="business_logic_language_identifier_agent",
    model=MODEL,
    description=(
        """
            Agent for analyzing the source code and creating a percentage breakdown
            of the programming languages in the source code. 
        """
    ),
    instruction=LANGUAGE_IDENTIFICATION_PROMPT,
    # output_key="languages_breakdown_percentage",
    tools=[identify_languages_from_source_code],
    disallow_transfer_to_parent=True,
)
