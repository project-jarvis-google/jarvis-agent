import logging
import os
from google.adk.tools import ToolContext
from pydantic import BaseModel

SUPPORTED_EXTENSIONS = (".java", ".cs", ".sql")

class RuleExtractionInput(BaseModel):
    successful: bool
    code_data: str
    message: str

import subprocess

def ask_gemini(query: str, tool_context: ToolContext) -> RuleExtractionInput:
    """
    Queries the codebase using the Gemini CLI.
    Passes the user's question or agent's task to the CLI context-aware engine.
    """
    repo_dir = tool_context.state.get("secure_temp_repo_dir")
    if not repo_dir or not os.path.exists(repo_dir):
        return RuleExtractionInput(successful=False, code_data="", message="Repository not found.")

    try:
        # Running gemini CLI with the query and including the repo directory
        result = subprocess.run(
            ["gemini", query, "--include-directories", repo_dir],
            capture_output=True,
            text=True,
            check=True
        )
        return RuleExtractionInput(successful=True, code_data=result.stdout, message="Successfully queried Gemini CLI.")
    except subprocess.CalledProcessError as e:
        return RuleExtractionInput(successful=False, code_data="", message=f"Gemini CLI failed: {e.stderr}")
    except Exception as e:
        return RuleExtractionInput(successful=False, code_data="", message=f"Error running Gemini CLI: {str(e)}")