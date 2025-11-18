"""
Defines the Component Design Agent, an LLM agent responsible for breaking down architectural plans into individual components.
"""

from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool

from app.utils.diagram_tools import plantuml_tool
from app.sub_agents.plantuml_diagramming_agent import plantuml_diagramming_agent
from .config import MODEL
from .prompt import AGENT_PROMPT

component_design_agent = Agent(
    name="component_design_agent",
    model=MODEL,
    instruction=AGENT_PROMPT,
    output_key="COMPONENT_OVERVIEW",
    tools=[plantuml_tool, AgentTool(agent=plantuml_diagramming_agent)],
)
