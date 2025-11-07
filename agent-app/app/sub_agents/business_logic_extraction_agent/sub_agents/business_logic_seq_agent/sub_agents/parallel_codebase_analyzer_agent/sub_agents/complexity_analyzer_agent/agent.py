from google.adk.agents import LlmAgent

from .tools import calculate_cyclomatic_complexity
from .prompt import main_prompt

MODEL = "gemini-2.5-flash"

complexity_analyzer_agent = LlmAgent(
    name="complexity_analyzer_agent",
    model=MODEL,
    description="Agent for calculating cyclomatic complexity.",
    instruction=main_prompt,
    tools=[calculate_cyclomatic_complexity],
    disallow_transfer_to_parent=True,
)