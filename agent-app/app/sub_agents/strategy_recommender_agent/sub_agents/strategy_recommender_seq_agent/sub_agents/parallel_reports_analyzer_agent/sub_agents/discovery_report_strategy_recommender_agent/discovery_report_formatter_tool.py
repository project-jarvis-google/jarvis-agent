import os
import json
import logging
from google.adk.tools import FunctionTool
from google.adk.tools import ToolContext
import uuid
from typing import Any

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _extract_client_name(full_text: str) -> str:
    """Finds the client name based on the 'Client:' marker."""
    client_marker = "Client: "
    start_index = full_text.find(client_marker)
    if start_index != -1:
        # Start after the marker
        start_index += len(client_marker)
        end_of_line = full_text.find('\n', start_index)
        date_marker_pos = full_text.find('Date:', start_index)
        possible_ends = [p for p in (end_of_line, date_marker_pos) if p != -1]
        end_index = min(possible_ends) if possible_ends else len(full_text)
        return full_text[start_index:end_index].strip()
    return "N/A"


def analyze_discovery_results(tool_context: ToolContext) -> bool:
    """
    Formats extracted PDF text from the context and prepares a summary prompt.
    This tool prepares the discovery report data for the aggregator agent.
    """
    logger.info("Starting discovery report data formatting.")
    is_report_formatted = False

    try:
        summary_text = tool_context.state.get("discovery_report_text")
        if not summary_text:
            logger.error("Tool context is missing 'state' for discovery_report_text.")
            return is_report_formatted

        client_name = _extract_client_name(summary_text)

        summary_prompt = (
            "**REPORT SECTIONS (Extract from the text below and format)**:\n\n"
            "**Executive Summary**\n"
            "**Pain Points**\n"
            "**Desired Outcomes**\n\n"
            "--- SOURCE TEXT ---\n"
            f"{summary_text}\n\n"
            "--- END SOURCE TEXT ---\n\n"
        )

        # Save the formatted discovery summary prompt to the state
        tool_context.state["discovery_summary_prompt"] = summary_prompt
        tool_context.state["client_name"] = client_name

        is_report_formatted = True
        logger.info("Discovery summary prompt created and saved to state.")
        return is_report_formatted

    except Exception as e:
        logger.error(f"An unexpected error occurred during data formatting: {e}", exc_info=True)
        return is_report_formatted

report_from_context_tool = FunctionTool(func=analyze_discovery_results)