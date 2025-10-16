import os
import json
import logging
from google.adk.tools import FunctionTool
from google.adk.tools import ToolContext
import uuid
from typing import Any

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

DISCOVERY_REPORT_GEMINI_PROMPT = """You are an expert Google Cloud Architect specializing in application modernization and migration. Your primary function is to act as a trusted advisor by meticulously inspecting a given discovery report.

## 6 R's Framework
- "rehost": {
    "name": "Rehost (Lift and Shift)",
    "description": "Moving an application to Google Cloud with minimal changes. This is the fastest migration path, often used for data center exits or for applications that are difficult to modify. It involves moving VMs to Google Compute Engine (GCE) or using Google Cloud VMware Engine (GCVE)."
},
- "replatform": {
    "name": "Replatform (Lift and Reshape)",
    "description": "Making minor cloud-native optimizations to an application to benefit from managed services without changing the core architecture. Examples include migrating a self-managed database to Cloud SQL, containerizing an app for Cloud Run or GKE Autopilot, or moving to a managed cache like Cloud Memorystore."
},
- "repurchase": {
    "name": "Repurchase (Drop and Shop)",
    "description": "Replacing an existing application with a new, cloud-native SaaS solution. This is ideal when the business function can be fulfilled by a standard, off-the-shelf product."
},
- "refactor": {
    "name": "Refactor/Rearchitect",
    "description": "Rearchitecting and rewriting an application to fully leverage cloud-native services and a microservices architecture. This is a significant investment but unlocks the highest benefits in scalability, agility, and cost optimization. It often involves migrating monolithic applications to microservices on GKE or Cloud Run, using services like Pub/Sub, Cloud Functions, and serverless databases like Firestore or Cloud Spanner."
},
- "retire": {
    "name": "Retire",
    "description": "Decommissioning applications that are no longer needed or providing business value. This simplifies the IT portfolio and reduces operational costs."
},
- "retain": {
    "name": "Retain",
    "description": "Keeping an application in its current on-premises or existing cloud environment. This is a valid strategy when migration is not justified due to high costs, compliance issues, or recent investment."
}

## Objective
Your mission is to analyze the Discovery agent report and act as a trusted advisor.
The report content is provided to you in the `report_from_context` field of your state.
Based on your analysis of the client's pain points, desired outcomes, and executive summary within that report, you will recommend one or more of the 6 R's migration strategies. Your recommendations must be grounded in Google Cloud's best practices and architecture framework.

## Core Instructions & Constraints
- Do not use general knowledge about what pain points, desired outcomes, and the executive summary are likely to occur.
- Evidence-Based Identification: Your identification and recommendations MUST be based purely on the input Discovery Report and the 6 R's framework.
- GCP-Centric Recommendations: All strategy recommendations must be justified with specific Google Cloud services and architectural patterns that address the client's needs.
- Do not show your work or any internal thinking. Only the result in the output format mentioned below and show nothing else.

## Output Format
The output should be a JSON object with the following keys:
- "pain_points": A list of strings, where each string is a pain point identified in the report.
- "desired_outcomes": A list of strings, where each string is a desired outcome identified in the report.
- "executive_summary": A string containing the executive summary from the report.
- "recommendations": A list of JSON objects, where each object has the following keys:
  - "strategy": A string with the recommended strategy from the 6 R's framework (e.g., "rehost", "refactor").
  - "justification": A string explaining *why* this strategy is recommended, linking it directly to the client's pain points and desired outcomes, and mentioning relevant GCP services.

Example:
```json
{
  "pain_points": [
    "Pain point 1 description.",
    "Pain point 2 description."
  ],
  "desired_outcomes": [
    "Desired outcome 1 description.",
    "Desired outcome 2 description."
  ],
  "executive_summary": "This is the executive summary of the report.",
  "recommendations": [
    {
      "strategy": "rehost",
      "justification": "Rehosting is recommended to quickly exit the on-premise data center, addressing the immediate pain point of hardware end-of-life. Moving to Google Compute Engine provides a fast path to the cloud with minimal application changes."
    },
    {
      "strategy": "refactor",
      "justification": "Refactoring the monolithic front-end into microservices on GKE is recommended to achieve the desired outcome of improved agility and independent scaling of services, directly addressing the pain point of slow deployment cycles."
    }
  ]
}
"""


def _extract_client_name(full_text: str) -> str:
    """Finds the client name based on the 'Client:' marker."""
    client_marker = "Client: "
    start_index = full_text.find(client_marker)
    if start_index != -1:
        # Start after the marker
        start_index += len(client_marker)

        # Find possible end points for the client name
        end_of_line = full_text.find("\n", start_index)
        date_marker_pos = full_text.find("Date:", start_index)

        # Filter out any markers that weren't found
        possible_ends = [p for p in (end_of_line, date_marker_pos) if p != -1]

        if possible_ends:
            end_index = min(possible_ends)
        else:
            # If no markers are found, take the rest of the string
            end_index = len(full_text)

        return full_text[start_index:end_index].strip()
    return "N/A"


def analyze_discovery_results(tool_context: ToolContext) -> bool:
    """
    Formats extract PDF text from the context and stores it back into the context.

    This tool prepares the data for analysis by a subsequent agent. It constructs a single
    report string from the executive_summary, pain_points, and desired_outcomes.

    Args:
        context: The shared context object. The type is set to 'Any' to avoid
            issues with automatic function calling schema generation.

    Returns:
        A string indicating that the data has been successfully formatted.
    """

    logger.info("Starting discovery report data formatting.")

    is_report_formatted = False

    try:
        # The context is passed as a dictionary, so we access its 'state' key.
        summary_text = tool_context.state.get("last_pdf_text")
        if not summary_text:
            message = "Tool context is missing 'state' for last_pdf_text."
            logger.error(message)
            return is_report_formatted

        # 2. Extract Client Name from the full text
        client_name = _extract_client_name(summary_text)

        summary_prompt = (
            "You are an expert report formatter. Your task is to extract and format "
            "the following information from the provided text into a SINGLE, "
            "continuous string. Do not add any conversational text or explanation. "
            "Maintain the exact content of the original sections, only adding the required headers.\n\n"
            "**Client Name**: " + client_name + "\n"
            "**REPORT SECTIONS (Extract from the text below and format)**:\n\n"
            "**Executive Summary**\n"
            "**Pain Points**\n"
            "**Desired Outcomes**\n\n"
            "--- SOURCE TEXT ---\n"
            f"{summary_text}\n\n"
            "--- END SOURCE TEXT ---\n\n"
            "**FINAL REPORT STRING FORMAT**:\n"
            "Client Name: [Extracted Name]\n"
            "Executive Summary:\n[Full Executive Summary Text]\n"
            "Pain Points:\n[Full Identified Pain Points Text]\n"
            "Desired Outcomes:\n[Full Desired Business Outcomes Text]\n\n"
            "Generate ONLY the content for the FINAL REPORT STRING FORMAT."
        )

        final_report_prompt = DISCOVERY_REPORT_GEMINI_PROMPT + "\n\n" + summary_prompt

        tool_context.state["final_report_prompt"] = final_report_prompt

        tool_context.state["client_name"] = client_name

        is_report_formatted = True

        # 3. Return a success message indicating the prompt is ready
        return is_report_formatted

    except Exception as e:
        logger.error(
            f"An unexpected error occurred during data formatting: {e}", exc_info=True
        )
        # 'rid' might not be defined if the error happened before its assignment.
        return is_report_formatted


report_from_context_tool = FunctionTool(func=analyze_discovery_results)
