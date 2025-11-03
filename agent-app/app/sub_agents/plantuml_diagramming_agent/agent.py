"""
Defines the plantuml diagramming agent which helps generating plantuml diagrams based on the user query.
"""

from google.adk.agents import Agent
from google.adk.planners import PlanReActPlanner
from google.adk.tools.google_search_tool import google_search
from google.adk.tools.url_context_tool import url_context

from .config import MODEL
from .prompt import AGENT_PROMPT

plantuml_diagramming_agent = Agent(
    name="plantuml_diagramming_agent",
    model=MODEL,
    instruction=AGENT_PROMPT,
    tools=[google_search, url_context],
    planner=PlanReActPlanner(),
)
