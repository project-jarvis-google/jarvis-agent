# agent.py
"""
Initializes and configures the main "Discovery Architect" agent.

This script sets up the agent's identity, loads its core instructions from
the prompt file, injects a knowledge base, and registers all available tools.
"""

import logging
import os

from google.adk.agents.llm_agent import LlmAgent

from app.config import MODEL

# --- Import custom tools and prompts ---
try:
    from .prompt import AGENT_INSTRUCTION
    from .tools import (
        compile_questions_to_sheet_tool,
        create_final_summary_pdf_tool,
        google_search_tool,
        read_and_update_sheet_tool,
    )

    ALL_TOOLS = [
        google_search_tool,
        compile_questions_to_sheet_tool,
        read_and_update_sheet_tool,
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
FINAL_INSTRUCTION = (
    f"{AGENT_INSTRUCTION}\n\n--- PRE-LOADED KNOWLEDGE BASE ---\n{KNOWLEDGE_INJECTION}"
)

# --- Define the Main Discovery Agent ---
discovery_architect_agent = LlmAgent(
    name="discovery_architect_agent",
    model=MODEL,
    instruction=FINAL_INSTRUCTION,
    tools=ALL_TOOLS,
)
logger.info("Discovery Architect Agent initialized successfully.")
