DISCOVERY_REPORT_FORMATTER_INSTRUCTION_TEMPLATE = """
### SYSTEM INSTRUCTION

Your primary role is to call the **analyze_discovery_results** tool to format the input discovery report data.

**CRITICAL INSTRUCTION:**

* Your response MUST ONLY be a tool call to **analyze_discovery_results**.
* DO NOT generate any text or conversational output.

### CRITICAL EXECUTION CHECK

**Before you consider calling the **analyze_discovery_results** tool, you MUST perform a check on the shared session state.**

1.  **REQUIRED STATE CHECK:** Check the shared `tool_context.state` object for the presence of the key **"discovery_report_text"**.
2.  **CONDITIONAL HALT:**
    * **IF** the key "discovery_report_text" is **missing or empty** (meaning the file upload and text extraction failed or was skipped), you **MUST NOT** call the tool. Instead, respond with the following single text message and **STOP**:
        `Analysis skipped: The Discovery Report text was not found in the shared context. Please ensure a valid PDF was uploaded in the previous step.`
    * **IF** the key "discovery_report_text" is present and contains text, proceed immediately to call the **analyze_discovery_results** tool to begin the analysis.
"""


def get_final_report_instruction(context):
    """
    Retrieves the dynamic prompt from the state.
    It returns one of two instructions:
    1. The instruction to call the tool (if data isn't prepared).
    2. The instruction to generate the final JSON (if data is prepared).
    """
    
    # Attempt to retrieve the prompt set by the previous tool
    prepared_prompt = context.state.get("discovery_summary_prompt")

    # --- STATE-AWARE CONTROL FLOW ---
    if prepared_prompt:
        # **STAGE 2 INSTRUCTION: The data is formatted, proceed to generate JSON.**
        # This instruction overrides the previous one and strictly forbids tool calls.
        return f"""
### SYSTEM INSTRUCTION

You are an expert at interpreting discovery reports. Your primary role is to generate a JSON object containing the key findings from the report summary provided below.

**CRITICAL INSTRUCTION:**

* Your response **MUST ONLY** be a JSON object.
* **DO NOT** add any conversational text, explanations, or markdown formatting like ```json.

### EMBEDDED REPORT SUMMARY

{prepared_prompt}
"""
    else:
        # **STAGE 1 INSTRUCTION: The data needs formatting, call the tool.**
        return DISCOVERY_REPORT_FORMATTER_INSTRUCTION_TEMPLATE