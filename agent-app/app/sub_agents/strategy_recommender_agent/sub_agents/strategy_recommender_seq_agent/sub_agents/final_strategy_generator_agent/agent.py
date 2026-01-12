from google.adk.agents import LlmAgent

from .prompt import get_final_strategy_instruction, save_final_json

MODEL = "gemini-2.5-pro"

final_strategy_generator_agent = LlmAgent(
    name="final_strategy_generator_agent",
    model=MODEL,
    description="Executes the aggregated prompt to generate the final JSON strategy recommendation.",
    instruction=get_final_strategy_instruction,
    # This agent has no tools to call, but it saves its output.
    tools=[save_final_json],
)
