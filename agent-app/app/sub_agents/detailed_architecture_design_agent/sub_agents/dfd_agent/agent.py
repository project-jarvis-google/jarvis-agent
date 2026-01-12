"""
Defines the Data Flow Diagram (DFD) Agent, an LLM agent responsible for generating DFDs based on architectural plans.
"""

from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool

from app.sub_agents.plantuml_diagramming_agent import plantuml_diagramming_agent
from app.utils.diagram_tools import plantuml_tool

from .config import MODEL
from .prompt import AGENT_PROMPT

dfd_agent = Agent(
    name="dfd_agent",
    model=MODEL,
    instruction=AGENT_PROMPT,
    output_key="DFD OVERVIEW",
    tools=[plantuml_tool, AgentTool(agent=plantuml_diagramming_agent)],
)
