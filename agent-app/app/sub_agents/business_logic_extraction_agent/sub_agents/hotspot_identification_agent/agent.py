from google.adk.agents import LlmAgent

from .hotspot_tools import identify_hotspots
from .prompt import HOTSPOT_IDENTIFICATION_PROMPT

MODEL = "gemini-2.5-flash"

hotspot_identification_agent = LlmAgent(
    name="hotspot_identification_agent",
    model=MODEL,
    description=(
        """
            Agent for identifying code hotspots using cyclomatic complexity 
            and business keyword heuristics.
        """
    ),
    instruction=HOTSPOT_IDENTIFICATION_PROMPT,
    tools=[identify_hotspots],
)