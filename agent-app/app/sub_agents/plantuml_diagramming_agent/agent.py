"""
Defines the plantuml diagramming agent which helps generating plantuml diagrams based on the user query.
"""
import os

from google.adk.agents import Agent
from google.adk.planners import PlanReActPlanner
from google.adk.tools.google_search_tool import google_search
from google.adk.tools.url_context_tool import url_context
from google.adk.tools.agent_tool import AgentTool

from ...utils.diagram_tools import plantuml_tool

from .config import MODEL
from .prompt import AGENT_PROMPT

def get_plantuml_diagramming_prompt() -> str:
    """Loads content from data files and injects it into placeholders within the AGENT_PROMPT."""
    prompt = AGENT_PROMPT
    current_dir = os.path.dirname(__file__)
    data_dir = os.path.join(current_dir, "data")
    injections = {}

    if os.path.isdir(data_dir):
        for filename in os.listdir(data_dir):
            file_path = os.path.join(data_dir, filename)
            if os.path.isfile(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    var_name = os.path.splitext(filename)[0]
                    injections[var_name] = content
                except Exception:
                    # Ignoring files that cannot be read
                    pass
    return prompt.format(**injections)

plantuml_diagramming_agent = Agent(
    name="plantuml_diagramming_agent",
    model=MODEL,
    instruction=get_plantuml_diagramming_prompt(),
    tools=[
        google_search,
        url_context
    ],
    planner=PlanReActPlanner(),
)
