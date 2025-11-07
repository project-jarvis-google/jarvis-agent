from google.adk.agents import LlmAgent

from .tools import generate_report
from .prompt import REPORT_GENERATOR_PROMPT

MODEL = "gemini-2.5-flash"

report_generator_agent = LlmAgent(
    name="report_generator_agent",
    model=MODEL,
    description=("Agent for generating a report on the source code analysis"),
    instruction=REPORT_GENERATOR_PROMPT,
    tools=[generate_report],
    output_key="generated_report",
)