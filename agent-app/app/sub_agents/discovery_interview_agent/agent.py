# agent.py
"""
Initializes and configures the main "Discovery Architect" agent.

This script sets up the agent's identity, loads its core instructions from
the prompt file, injects a knowledge base, and registers all available tools.
"""

import logging
import os
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
        create_final_summary_pdf_tool,
        google_search_tool,
    )

    ALL_TOOLS: list[Callable[..., Any] | BaseTool | BaseToolset] = [
        google_search_tool,
        create_final_summary_pdf_tool,
    ]

except ImportError as e:
    logging.error(
        f"Failed to import tools or prompts: {e}. Ensure all files are in the correct directory."
    )
    exit(1)

logger = logging.getLogger(__name__)


# --- Function to load knowledge from local files ---
def load_knowledge_base():
    """
    Reads all .txt files from the 'knowledge_base' directory and formats them
    into a single string to be injected into the agent's prompt.
    """
    knowledge = {}
    kb_path = os.path.join(os.path.dirname(__file__), "knowledge_base")
    if not os.path.exists(kb_path):
        logger.warning(
            "knowledge_base directory not found. Agent will have no reference material."
        )
        return ""

    for filename in os.listdir(kb_path):
        if filename.endswith(".txt"):
            topic = filename.replace(".txt", "").replace("_", " ")
            with open(os.path.join(kb_path, filename)) as f:
                knowledge[topic] = f.read()

    formatted_knowledge = "\n\n".join(
        [
            f"## Reference for: {topic}\n{content}"
            for topic, content in knowledge.items()
        ]
    )
    return formatted_knowledge


# --- "Memorize" the knowledge at startup ---
KNOWLEDGE_INJECTION = load_knowledge_base()
FINAL_INSTRUCTION = f"""{AGENT_INSTRUCTION}\n\n
        --- PRE-LOADED KNOWLEDGE BASE ---\n
        <GROUNDING_SOURCE_TRUTH>
            IMPORTANT: The following content is your ONLY acceptable agenda. 
            You are prohibited from skipping any bullet point listed within these sections.
            {KNOWLEDGE_INJECTION}
        </GROUNDING_SOURCE_TRUTH>
    """


# --- Define the Main Discovery Agent ---
discovery_architect_agent = LlmAgent(
    name="discovery_architect_agent",
    model=MODEL,
    instruction=FINAL_INSTRUCTION,
    tools=ALL_TOOLS,
)
logger.info("Discovery Architect Agent initialized successfully.")
