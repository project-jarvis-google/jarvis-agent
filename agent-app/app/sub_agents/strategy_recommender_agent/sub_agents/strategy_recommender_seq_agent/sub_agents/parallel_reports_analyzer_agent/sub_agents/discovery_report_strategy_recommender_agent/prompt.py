# ==============================================================================
# File: prompt.py
# ==============================================================================

# Define a static instruction template for the first stage (Tool Calling)
# Note: The embedded prompt is no longer needed in the instruction for Stage 1.
FINAL_REPORT_INSTRUCTION_TEMPLATE = """
### SYSTEM INSTRUCTION

Your primary role is to call the **analyze_discovery_results** tool to format the input data and generate the final prompt for the strategy recommendation.

**IMPORTANT INSTRUCTIONS:**

* Your response MUST ONLY be a tool call to **analyze_discovery_results**.

* DO NOT wrap the tool call in `print()` or include any other text.

### CRITICAL EXECUTION CHECK

**Before you consider calling the **analyze_discovery_results** tool, you MUST perform a check on the shared session state.**

1.  **REQUIRED STATE CHECK:** Check the shared `tool_context.state` object for the presence of the key **"last_pdf_text"**.
2.  **CONDITIONAL HALT:**
    * **IF** the key "last_pdf_text" is **missing or empty** (meaning the file upload and text extraction failed or was skipped), you **MUST NOT** call the tool. Instead, respond with the following single text message and **STOP**:
        `Analysis skipped: The Discovery Report text was not found in the shared context. Please ensure a valid PDF was uploaded in the previous step.`
    * **IF** the key "last_pdf_text" is present and contains text, proceed immediately to call the **analyze_discovery_results** tool to begin the analysis.
"""


# Define the dynamic function that the LLMAgent will use
def get_final_report_instruction(context):
    """
    Retrieves the dynamic prompt from the state.
    It returns one of two instructions:
    1. The instruction to call the tool (if data isn't prepared).
    2. The instruction to generate the final JSON (if data is prepared).
    """

    # Attempt to retrieve the prompt set by the previous tool
    prepared_prompt = context.state.get("final_report_prompt")

    # --- STATE-AWARE CONTROL FLOW ---
    if prepared_prompt:
        # **STAGE 2 INSTRUCTION: The data is formatted, proceed to generate the final JSON.**
        # This instruction overrides the previous one and strictly forbids tool calls.
        return f"""
### SYSTEM INSTRUCTION

Your primary role is to act as an expert Google Cloud Architect and generate the final strategy recommendation.

**CRITICAL INSTRUCTION:**

* Your response **MUST ONLY** be the JSON object as defined in the 'Output Format' section embedded in the prompt below.
* **DO NOT** call any tools.
* **DO NOT** add any conversational text, explanations, or markdown text outside of the final JSON object (no wrappers, no print statements).

### EMBEDDED PROMPT (Use this prompt to generate your response)

{prepared_prompt}
"""
    else:
        # **STAGE 1 INSTRUCTION: The data needs formatting, call the tool.**
        return FINAL_REPORT_INSTRUCTION_TEMPLATE
