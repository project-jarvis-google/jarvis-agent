from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from .pdf_generator_tool import generate_and_save_pdf_tool
from .prompt import REPORT_GENERATION_PROMPT

MODEL = "gemini-2.5-flash"

strategy_report_generator_agent = LlmAgent(
    name="strategy_report_generator_agent",
    model=MODEL,
    description=(
        "Agent for creating a Strategy Recommendation report from the output of previous agent."
    ),
    instruction=REPORT_GENERATION_PROMPT,
    tools=[generate_and_save_pdf_tool],
)


session_service = InMemorySessionService()

runner = Runner(
    agent=strategy_report_generator_agent,
    app_name="report_generator_app",
    session_service=session_service,
)
