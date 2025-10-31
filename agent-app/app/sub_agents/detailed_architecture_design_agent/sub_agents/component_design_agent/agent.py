"""
Defines the Component Design Agent, an LLM agent responsible for breaking down architectural plans into individual components.
"""

from google.adk.agents import LlmAgent

from .config import MODEL
from .prompt import AGENT_PROMPT

component_design_agent = LlmAgent(
    name="component_design_agent",
    model=MODEL,
    description=(
        "Helps breakdown the architectural plan into components which can constitute the required solution."
    ),
    instruction=AGENT_PROMPT,
    output_key="COMPONENT_OVERVIEW",
)
