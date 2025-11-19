import logging

from google.adk.tools import FunctionTool, ToolContext

from .common_prompt import FINAL_STRATEGY_PROMPT

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def aggregate_and_prepare_final_prompt(tool_context: ToolContext) -> bool:
    """
    Aggregates outputs from parallel agents (discovery and tech stack)
    and constructs the final prompt for the strategy generation agent.
    """
    logger.info("Aggregating parallel agent outputs and preparing final prompt.")
    is_prompt_prepared = False

    try:
        # 1. Get the mandatory discovery report summary prompt
        discovery_summary_prompt = tool_context.state.get("discovery_summary_prompt")
        if not discovery_summary_prompt:
            logger.error("Mandatory 'discovery_summary_prompt' not found in state.")
            # We can't proceed without this.
            return is_prompt_prepared

        # 2. Get the optional tech stack summary
        # This will be present if the tech stack agent ran successfully.
        tech_stack_summary = tool_context.state.get("formatted_tech_stack_data")

        # 3. Build the final combined prompt
        final_prompt_sections = [FINAL_STRATEGY_PROMPT, discovery_summary_prompt]

        if tech_stack_summary:
            logger.info("Tech stack summary found. Appending to final prompt.")
            tech_stack_section = (
                "\n\n**ADDITIONAL CONTEXT (from Tech Stack Profile)**:\n"
                f"{tech_stack_summary}"
            )
            final_prompt_sections.append(tech_stack_section)

        # 4. Combine all parts and save to state for the next agent
        final_combined_prompt = "\n".join(final_prompt_sections)
        tool_context.state["final_strategy_generation_prompt"] = final_combined_prompt

        is_prompt_prepared = True
        logger.info(
            "Final strategy generation prompt has been successfully prepared and saved to state."
        )

    except Exception as e:
        logger.error(
            f"An unexpected error occurred during final prompt aggregation: {e}",
            exc_info=True,
        )

    return is_prompt_prepared


final_report_aggregator_tool = FunctionTool(func=aggregate_and_prepare_final_prompt)
