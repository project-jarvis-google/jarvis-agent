# tools.py
from google.adk.tools import FunctionTool, ToolContext

def transfer_to_discovery_agent(initial_prompt: str, tool_context: ToolContext) -> str:
    """
    Transfers the conversation to the specialized discovery architect agent.

    Args:
        initial_prompt: The user's initial request to pass to the sub-agent.
    """
    tool_context.actions.transfer_to_agent = "discovery_architect_agent"
    return f"Understood. Transferring you to the Discovery Architect to begin the process..."

transfer_to_discovery_agent_tool = FunctionTool(func=transfer_to_discovery_agent)