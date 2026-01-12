def get_final_strategy_instruction(context):
    """
    Retrieves the final, aggregated prompt from the state and instructs the
    agent to generate the final JSON output.
    """
    # 1. Retrieve the master prompt prepared by the aggregator agent.
    final_prompt = context.state.get("final_strategy_generation_prompt")

    if not final_prompt:
        # This is a fallback. If the aggregator failed, the agent will halt.
        return "ERROR: The final strategy generation prompt was not found in the state. Cannot proceed."

    # 2. The instruction is simply the master prompt itself.
    #    The master prompt contains all the rules for generating the final JSON.
    return final_prompt


def save_final_json(tool_context, llm_response: str) -> str:
    """Saves the raw LLM response (the final JSON) to the state."""
    tool_context.state["final_recommendation_json"] = llm_response
    return "Final JSON recommendation has been saved to the state."
