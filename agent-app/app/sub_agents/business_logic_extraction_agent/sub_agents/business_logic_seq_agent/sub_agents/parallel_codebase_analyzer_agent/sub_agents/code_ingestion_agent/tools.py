import os
import subprocess

def clone_git_repository(repo_url: str) -> str:
    """
    Clones a git repository to a local directory.
    """
    clone_dir = f"/tmp/cloned_repo/{os.path.basename(repo_url)}"
    subprocess.run(["git", "clone", repo_url, clone_dir])
    return clone_dir

def analyze_languages(path: str) -> dict:
    """
    Analyzes the files in a directory to identify the programming languages.
    """
    languages = set()
    language_map = {
        ".java": "Java",
        ".cs": "C#",
        ".sql": "SQL",
    }
    for root, _, files in os.walk(path):
        for file in files:
            ext = os.path.splitext(file)[1]
            if ext in language_map:
                languages.add(language_map[ext])
    return {"languages": list(languages)}
