from google.adk.agents import LlmAgent

from .final_report_aggregator_tool import final_report_aggregator_tool
from .prompt import get_aggregator_instruction

MODEL = "gemini-2.5-flash"

final_report_aggregator_agent = LlmAgent(
    name="final_report_aggregator_agent",
    model=MODEL,
    description="Aggregates outputs from parallel analysis agents and prepares the final prompt for the report generator.",
    instruction=get_aggregator_instruction,
    tools=[final_report_aggregator_tool],
)
