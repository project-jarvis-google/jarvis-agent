"""
Defines the API Spec Agent, an LLM agent responsible for creating API specifications for the planned services.
"""

from google.adk.agents import Agent

from .config import MODEL
from .prompt import AGENT_PROMPT

api_spec_agent = Agent(
    name="api_spec_agent",
    model=MODEL,
    instruction=AGENT_PROMPT,
    output_key="API_SPECIFICATIONS",
)
