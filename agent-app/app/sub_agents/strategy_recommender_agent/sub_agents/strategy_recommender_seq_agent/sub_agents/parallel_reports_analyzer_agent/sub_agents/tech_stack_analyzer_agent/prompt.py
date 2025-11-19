# Define a static instruction template for the first stage (Tool Calling)
TECH_STACK_FORMATTER_INSTRUCTION_TEMPLATE = """
### SYSTEM INSTRUCTION

Your primary role is to call the **format_tech_stack_data** tool to format the input tech stack data.

**IMPORTANT INSTRUCTIONS:**

* Your response MUST ONLY be a tool call to **format_tech_stack_data**.
* DO NOT wrap the tool call in `print()` or include any other text.

### CRITICAL EXECUTION CHECK

**Before you consider calling the **format_tech_stack_data** tool, you MUST perform a check on the shared session state.**

1.  **REQUIRED STATE CHECK:** Check the shared `tool_context.state` object for the presence of the key **"tech_stack_full_text"**.
2.  **CONDITIONAL HALT:**
    * **IF** the key "tech_stack_full_text" is **missing or empty** (meaning the tech stack PDF was not provided or extraction failed), you **MUST NOT** call the tool. Instead, respond with the following single text message and **STOP**:
        `Tech stack analysis skipped: The Tech Stack Profile text was not found in the shared context. This report is optional, so analysis will proceed without it.`
    * **IF** the key "tech_stack_full_text" is present and contains text, proceed immediately to call the **format_tech_stack_data** tool to begin the formatting.
"""


# Define the dynamic function that the LLMAgent will use
def get_tech_stack_instruction(context):
    """
    Retrieves the dynamic prompt from the state.
    It returns one of two instructions:
    1. The instruction to call the tool (if data isn't prepared).
    2. The instruction to generate the final JSON (if data is prepared).



    """
    # Attempt to retrieve the formatted tech stack data
    formatted_tech_stack_data = context.state.get("formatted_tech_stack_data")

    # --- STATE-AWARE CONTROL FLOW ---
    if formatted_tech_stack_data:
        # **STAGE 2 INSTRUCTION: The data is formatted, proceed to analyze/summarize.**
        # This instruction overrides the previous one and strictly forbids tool calls.
        return f"""
### SYSTEM INSTRUCTION

You are an expert in analyzing application tech stacks. Your primary role is to summarize the provided tech stack information.

**CRITICAL INSTRUCTION:**

* Your response **MUST ONLY** be a concise summary of the tech stack.
* **DO NOT** call any tools.
* **DO NOT** add any conversational text or explanations.

### EMBEDDED TECH STACK DATA

{formatted_tech_stack_data}
"""
    else:
        # **STAGE 1 INSTRUCTION: The data needs formatting, call the tool.**
        return TECH_STACK_FORMATTER_INSTRUCTION_TEMPLATE
