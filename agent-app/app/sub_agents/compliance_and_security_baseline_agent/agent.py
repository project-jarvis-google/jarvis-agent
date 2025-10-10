# agent.py
from google.adk.agents import Agent
from ...config import MODEL
from .prompt import COMPLIANCE_AGENT_PROMPT
# Changed csv_reader_tool to the new tool name
from .tools import create_gcs_file_tool, process_and_upload_csv_tool

compliance_agent = Agent(
    name="compliance_security_agent",
    model=MODEL,
    description="Analyzes applications and generates a downloadable compliance report from text or CSV input.",
    instruction=COMPLIANCE_AGENT_PROMPT,
    # Updated the tool list with the new tool
    tools=[create_gcs_file_tool, process_and_upload_csv_tool],
)