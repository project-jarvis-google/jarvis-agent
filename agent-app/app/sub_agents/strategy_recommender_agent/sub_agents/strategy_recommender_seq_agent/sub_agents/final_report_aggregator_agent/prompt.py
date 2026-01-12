def get_aggregator_instruction(context):
    """
    Retrieves the dynamic prompt for the final report aggregator agent.
    It instructs the agent to call the aggregation tool once, then exit.
    """
    # Check if the final prompt has already been prepared and saved to state
    if context.state.get("final_strategy_generation_prompt"):
        # If it's already prepared, the agent's job is done.
        # Instruct it to respond with a success message and stop.
        return "Final strategy generation prompt successfully prepared. Aggregation complete."
    else:
        # If not prepared, instruct the agent to call the tool.
        return """
### SYSTEM INSTRUCTION

Your sole purpose is to aggregate the analysis from the previous parallel steps and prepare the final prompt for strategy generation.

**CRITICAL INSTRUCTION:**

* Your response MUST ONLY be a tool call to **aggregate_and_prepare_final_prompt**. This tool should only be called ONCE.
* DO NOT generate any text or conversational output.

"""
