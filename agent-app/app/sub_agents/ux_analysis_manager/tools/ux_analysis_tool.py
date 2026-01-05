# ux_analysis_tool.py

import json
from google.adk.tools import BaseTool
from ..sub_agents.dynamic_analysis_manager.dynamic_analysis_tools import LogAnalysisTool  # pure function parser


class LogAnalysisToolWrapper(BaseTool):
    """
    ADK Tool wrapper that exposes LogAnalysisTool as a callable ADK Tool.
    """

    def __init__(self):
        super().__init__(
            name="log_analysis_tool",
            description="Validates and normalizes raw UX logs into canonical JSON."
        )

    # Define input schema so ADK knows argument names.
    inputs = {
        "raw_log_text": {
            "type": "string",
            "description": "The raw log file contents uploaded by the user."
        },
        "file_type": {
            "type": "string",
            "enum": ["csv", "tsv", "json", "ndjson", "txt"],
            "description": "The format of the uploaded log."
        }
    }

    def run(self, raw_log_text: str, file_type: str):
        data = LogAnalysisTool(raw_log_text, file_type)
        # Must return JSON-serializable data; returning string is safest for the LLM.
        return json.dumps(data)
        
