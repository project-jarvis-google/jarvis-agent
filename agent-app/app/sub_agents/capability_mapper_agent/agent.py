# agent.py
"""
Initializes and configures the "Business Capability Mapper" agent.
"""

import logging
from collections.abc import Callable
from typing import Any

from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools import BaseTool
from google.adk.tools.base_toolset import BaseToolset

from app.config import MODEL

# --- Import custom tools and prompts ---
try:
    from .prompt import AGENT_INSTRUCTION
    from .tools import (
        generate_capability_report_csv_tool,
        map_capabilities_to_inventory_tool,
    )

    ALL_TOOLS: list[Callable[..., Any] | BaseTool | BaseToolset] = [
        map_capabilities_to_inventory_tool,
        generate_capability_report_csv_tool,
    ]

except ImportError as e:
    logging.error(
        "Failed to import tools or prompts: %s. Ensure all files are in the correct directory.",
        e,
    )
    exit(1)

logger = logging.getLogger(__name__)

# --- Define the Main Capability Mapper Agent ---
capability_mapper_agent = LlmAgent(
    name="capability_mapper_agent",
    model=MODEL,
    instruction=AGENT_INSTRUCTION,
    tools=ALL_TOOLS,
)
logger.info("Business Capability Mapper Agent initialized successfully.")
