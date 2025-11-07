from google.adk.agents import LlmAgent

from .tools import find_business_keywords
from .prompt import main_prompt

MODEL = "gemini-2.5-flash"

keyword_analyzer_agent = LlmAgent(
    name="keyword_analyzer_agent",
    model=MODEL,
    description="Agent for identifying and flagging code blocks containing common business logic keywords.",
    instruction=main_prompt,
    tools=[find_business_keywords],
    disallow_transfer_to_parent=True,
)