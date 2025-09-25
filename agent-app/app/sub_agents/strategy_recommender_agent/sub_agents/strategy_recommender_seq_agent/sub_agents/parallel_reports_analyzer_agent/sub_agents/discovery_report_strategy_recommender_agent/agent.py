from google.adk.agents import LlmAgent
from .discovery_report_formatter_tool import report_from_context_tool
from .prompt import get_final_report_instruction



MODEL = "gemini-2.5-pro"

# Agent for Step 1: Format the data using a tool
discovery_report_strategy_recommender_agent = LlmAgent(
    name="report_formatter",
    model=MODEL,
    description="Agent that generates the final strategy recommendation based on the prompt in the agent state.",
    instruction=get_final_report_instruction,
    tools=[report_from_context_tool],
)


