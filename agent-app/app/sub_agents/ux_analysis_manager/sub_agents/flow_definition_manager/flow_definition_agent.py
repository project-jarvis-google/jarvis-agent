# agent.py
from google.adk.agents import LlmAgent

from .flow_definition_agent_prompt import AGENT_INSTRUCTION, DESCRIPTION

# from .flow_manageger_tools import SaveImageTool, StitchFlowTool
# No tools needed for this simplified version

MODEL = "gemini-2.5-pro"

# Define the agent
flow_definition_agent = LlmAgent(
    name="flow_definition_agent",
    model=MODEL,
    description=DESCRIPTION,
    instruction=AGENT_INSTRUCTION,
    # tools=[
    # SaveImageTool(
    # name="save_image",
    # description="Saves an uploaded image file to the local project assets folder."
    # ),
    # StitchFlowTool(
    # name="stitch_flow",
    # description="Stitches multiple saved images vertically into a single flow diagram image."
    # )
    # ],
)
