import logging

from google.adk.tools import FunctionTool, ToolContext

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def format_tech_stack_data(tool_context: ToolContext) -> bool:
    """
    Extracts and formats the tech stack profile text from the context.
    This tool prepares the tech stack data for analysis by a subsequent agent.
    """
    logger.info("Starting tech stack data formatting.")

    is_tech_stack_formatted = False

    try:
        tech_stack_text = tool_context.state.get("tech_stack_full_text")
        if not tech_stack_text:
            message = "Tool context is missing 'state' for tech_stack_full_text."
            logger.warning(message)
            return is_tech_stack_formatted  # It's optional, so we don't error out, just indicate it wasn't formatted.

        tool_context.state["formatted_tech_stack_data"] = tech_stack_text
        is_tech_stack_formatted = True

    except Exception as e:
        logger.error(
            f"An unexpected error occurred during tech stack data formatting: {e}",
            exc_info=True,
        )

    return is_tech_stack_formatted


tech_stack_formatter_tool = FunctionTool(func=format_tech_stack_data)
