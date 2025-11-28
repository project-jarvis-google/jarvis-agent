from google.adk.agents import SequentialAgent


from .sub_agents.source_code_staging_agent import business_logic_source_code_staging_agent
from .sub_agents.language_identifier_agent import business_logic_language_identifier_agent


MODEL = "gemini-1.5-flash"

business_logic_seq_agent = SequentialAgent(
    name="business_logic_seq_agent",
    description=(
        """Executes a sequence of repository preparation, code analysis and report building"""
    ),
    sub_agents=[
        business_logic_source_code_staging_agent,
        business_logic_language_identifier_agent,
    ],
)
