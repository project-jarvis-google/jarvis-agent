"""
Defines the Deployment Architecture Agent, an LLM agent responsible for generating the deployment architecture based on architectural plans.
"""

from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool

from .....utils.diagram_tools import plantuml_tool
from ....plantuml_diagramming_agent import plantuml_diagramming_agent
from .config import MODEL
from .prompt import AGENT_PROMPT

deployment_architect_agent = Agent(
    name="deployment_architect_agent",
    model=MODEL,
    instruction=AGENT_PROMPT,
    output_key="Deployment Architecture Overview",
    tools=[plantuml_tool, AgentTool(agent=plantuml_diagramming_agent)],
)
