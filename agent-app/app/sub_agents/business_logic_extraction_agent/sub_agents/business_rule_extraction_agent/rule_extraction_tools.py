import logging
import os
from google.adk.tools import ToolContext
from pydantic import BaseModel

SUPPORTED_EXTENSIONS = (".java", ".cs", ".sql")

class RuleExtractionInput(BaseModel):
    successful: bool
    code_data: str
    message: str

def read_target_files(tool_context: ToolContext) -> RuleExtractionInput:
    """
    Retrieves source code for analysis. 
    Walks through the repository and reads all supported files (.java, .cs, .sql).
    Adds line numbers to the content to assist with source linking.
    """
    repo_dir = tool_context.state.get("secure_temp_repo_dir")
    if not repo_dir or not os.path.exists(repo_dir):
        return RuleExtractionInput(successful=False, code_data="", message="Repository not found.")

    combined_output = []
    file_count = 0

    for root, _, filenames in os.walk(repo_dir):
        for filename in filenames:
            if filename.lower().endswith(SUPPORTED_EXTENSIONS):
                file_path = os.path.join(root, filename)
                rel_path = file_path.replace(repo_dir, "").lstrip(os.sep)
                
                try:
                    with open(file_path, "r", errors="ignore") as f:
                        lines = f.readlines()
                        numbered_lines = [f"{i+1}: {line}" for i, line in enumerate(lines)]
                        combined_output.append(f"--- FILE: {rel_path} ---\n" + "".join(numbered_lines) + "\n")
                        file_count += 1
                except Exception as e:
                    logging.warning(f"Failed to read {file_path}: {e}")

    if not combined_output:
        return RuleExtractionInput(successful=False, code_data="", message="No supported source files found.")

    return RuleExtractionInput(successful=True, code_data="\n".join(combined_output), message=f"Read {file_count} files.")