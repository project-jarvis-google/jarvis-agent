# halt_tool.py
from typing import Any

from google.adk.tools import FunctionTool, ToolContext


def halt_workflow(tool_context: ToolContext) -> dict[str, Any]:
    """
    Explicitly signals the SequentialAgent to halt the workflow.
    The status 'PAUSE_REQUIRED' is a convention that the SequentialAgent
    framework can be configured to interpret as a stop condition.
    """
    # Note: Returning a non-success status code (like an HTTP 4xx or a custom enum)
    # is often how frameworks are designed to handle intentional breaks.
    # We will use a unique string status that the coordinator can intercept if needed.
    return {
        "status": "HALT_WORKFLOW",
        "message": "File not uploaded. Workflow halted by staging agent.",
    }


halt_workflow_tool = FunctionTool(func=halt_workflow)
