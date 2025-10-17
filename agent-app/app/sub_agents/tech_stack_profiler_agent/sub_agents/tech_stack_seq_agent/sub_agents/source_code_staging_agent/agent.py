from google.adk.agents import LlmAgent

from .prompt import SOURCE_CODE_STAGING_PROMPT
from .source_code_tools import fetch_source_code_from_git_repo

MODEL = "gemini-2.5-flash"

source_code_staging_agent = LlmAgent(
    name="source_code_staging_agent",
    model=MODEL,
    description=("Agent for creating a temporary storage for source code analysis"),
    instruction=SOURCE_CODE_STAGING_PROMPT,
    tools=[fetch_source_code_from_git_repo],
)
