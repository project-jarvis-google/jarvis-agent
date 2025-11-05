# tools.py
from google.adk.tools import FunctionTool, ToolContext


def _create_transfer_tool(agent_name: str, description: str) -> FunctionTool:
    """A factory to create a specialized agent transfer tool."""

    def transfer_func(tool_context: ToolContext) -> str:
        """
        Transfers the conversation to a specialized sub-agent.
        (This docstring will be dynamically updated by the factory)
        """
        tool_context.actions.transfer_to_agent = agent_name

        # # Create a user-friendly name from the agent_name
        agent_friendly_name = (
            agent_name.replace("_", " ").replace("agent", "Agent").title()
        )

        return f"Understood. Transferring you to the {agent_friendly_name}..."

    # Give the dynamically created function a proper name and docstring
    # for the ADK to inspect.
    transfer_func.__name__ = f"transfer_to_{agent_name}"
    transfer_func.__doc__ = f"""
    {description}

    Args:
        initial_prompt: The user's initial request to pass to the sub-agent.
    """

    # Create the FunctionTool using the new function
    return FunctionTool(func=transfer_func)


# --- Create your specific tools using the factory ---

transfer_to_discovery_agent_tool = _create_transfer_tool(
    agent_name="discovery_architect_agent",
    description="Transfers the conversation to the specialized Discovery Architect agent.",
)

transfer_to_capability_mapper_agent_tool = _create_transfer_tool(
    agent_name="capability_mapper_agent",
    description="Transfers the conversation to the specialized Business Capability Mapper agent.",
)

transfer_to_strategy_recommender_agent_tool = _create_transfer_tool(
    agent_name="strategy_recommender_agent",
    description="Transfers the conversation to the specialized Strategy Recommendation agent.",
)

transfer_to_detailed_architecture_design_agent_tool = _create_transfer_tool(
    agent_name="detailed_architecture_design_agent",
    description="Transfers the conversation to the specialized Detailed Architecture Design agent.",
)
