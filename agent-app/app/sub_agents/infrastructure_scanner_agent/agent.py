from google.adk.agents import LlmAgent

# from .writer import save_generated_report_py
from .config import MODEL
from .prompt import AGENT_PROMPT

infra_scanner_agent = LlmAgent(
    name="infrastructure_scanner_agent",
    model=MODEL,
    description=("Builds a comprehensive picture of the client's infrastructure."),
    instruction=AGENT_PROMPT,
)
