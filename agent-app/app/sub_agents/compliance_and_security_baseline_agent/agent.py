# agent.py
from google.adk.agents import Agent

from ...config import MODEL
from .prompt import COMPLIANCE_AGENT_PROMPT
from .tools import csv_tool, github_tool, pdf_tool

compliance_agent = Agent(
    name="compliance_security_agent",
    model=MODEL,
    description="Analyzes applications for compliance via CSV, text, or by inspecting GitHub repositories.",
    instruction=COMPLIANCE_AGENT_PROMPT,
    # Register the tools
    tools=[pdf_tool, csv_tool, github_tool],
)
