from google.adk.agents import LlmAgent
from .prompt import get_tech_stack_instruction
from .tech_stack_formatter_tool import tech_stack_formatter_tool

MODEL = "gemini-2.5-flash"

# Agent for Step 1: Format the data using a tool
tech_stack_analyzer_agent = LlmAgent(
    name="tech_stack_analyzer_agent",
    model=MODEL,
    description="Agent that formats and analyzes the tech stack profile report.",
    instruction=get_tech_stack_instruction,
    tools=[tech_stack_formatter_tool],
)

