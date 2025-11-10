# github_tools.py
import logging
import os

from github import Github, GithubException
from google.adk.tools import FunctionTool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _get_github_client():
    token = os.getenv("GITHUB_PAT")
    if not token:
        raise ValueError("GITHUB_PAT environment variable is missing.")
    return Github(token)


# --- UPDATED SIGNATURE: added optional specific_file_path ---
def fetch_repo_compliance_context(
    repo_name: str, specific_file_path: str | None = None
) -> str:
    """
    Fetches compliance-relevant files from a GitHub repository.
    If 'specific_file_path' is provided, it fetches ONLY that file.
    If NOT provided, it scans for standard documentation (README, SECURITY.md).
    """
    try:
        g = _get_github_client()
        repo = g.get_repo(repo_name)
    except Exception as e:
        return f"Error connecting to GitHub: {e}"

    # --- MODE 1: Specific File Requested by User ---
    if specific_file_path:
        try:
            file_content = repo.get_contents(specific_file_path)
            decoded = file_content.decoded_content.decode("utf-8")
            # Truncate huge files to prevent context window overflow
            if len(decoded) > 30000:
                decoded = decoded[:30000] + "\n...[TRUNCATED]..."

            return (
                f"### CONTENT OF {specific_file_path} in {repo_name} ###\n\n{decoded}"
            )
        except GithubException as e:
            if e.status == 404:
                return f"ERROR: The file '{specific_file_path}' does not exist in repository '{repo_name}'. Please ask the user to check the path."
            return f"Error fetching file: {e}"

    # --- MODE 2: Default Scan (No specific file provided) ---
    target_files = ["README.md", "SECURITY.md", "ARCHITECTURE.md", "docs/compliance.md"]
    found_content = []
    found_content.append(f"# Compliance Scan for Repo: {repo.full_name}")

    files_found = 0
    for file_path in target_files:
        try:
            content = repo.get_contents(file_path).decoded_content.decode("utf-8")
            if len(content) > 15000:
                content = content[:15000] + "\n...[TRUNCATED]..."
            found_content.append(f"\n## File: {file_path}\n{content}")
            files_found += 1
        except GithubException:
            continue  # File just doesn't exist, move to next

    if files_found == 0:
        # CRITICAL: Return a specific flag that the Prompt can recognize
        return "STATUS: NO_STANDARD_DOCS_FOUND. Do not generate a report yet. Ask the user for a specific file path."

    return "\n".join(found_content)


github_reader_tool = FunctionTool(fetch_repo_compliance_context)
