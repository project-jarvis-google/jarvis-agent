from google.adk.agents import LlmAgent

from .prompt import main_prompt

MODEL = "gemini-2.5-flash"

rule_extraction_agent = LlmAgent(
    name="rule_extraction_agent",
    model=MODEL,
    description="Agent for translating complex code logic into simple, human-readable 'IF-THEN' rules.",
    instruction=main_prompt,
    tools=[], # This agent primarily uses the LLM for NLP, so no specific tools are defined here.
    disallow_transfer_to_parent=True,
)
