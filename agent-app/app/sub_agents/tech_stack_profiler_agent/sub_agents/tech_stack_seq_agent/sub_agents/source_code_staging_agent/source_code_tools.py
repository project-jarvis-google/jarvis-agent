import tempfile
import os
import shutil
from git import Repo
from google.adk.tools import ToolContext

import logging

# TODO: Create same for Gitlab, Bitbucket, SSM


def fetch_source_code_from_git_repo(
    git_repo_url: str, access_token: str, tool_context: ToolContext
) -> bool:
    sourceCodeStored = False
    custom_temp_path = os.getenv("CUSTOM_TEMP_PATH")
    logging.info("git_repo_url => %s", git_repo_url)
    logging.info("access_token => %s", access_token)
    try:
        secure_temp_repo_dir = tempfile.mkdtemp(dir=custom_temp_path)
        logging.info("secure_temp_repo_dir => %s", secure_temp_repo_dir)
        logging.info("os.path.exists => %s", os.path.exists(secure_temp_repo_dir))
        url_with_token = git_repo_url.replace(
            "https://", f"https://{access_token}:x-oauth-basic@"
        )
        logging.info("url_with_token => %s", url_with_token)
        Repo.clone_from(url_with_token, secure_temp_repo_dir)
    except Exception as e:
        logging.error("Exception occurred: %s", e)
        logging.error(
            "except 'secure_temp_repo_dir' in locals() => %s",
            ("secure_temp_repo_dir" in locals()),
        )
        logging.error(
            "except os.path.exists => %s", os.path.exists(secure_temp_repo_dir)
        )
        if "secure_temp_repo_dir" in locals() and os.path.exists(secure_temp_repo_dir):
            shutil.rmtree(secure_temp_repo_dir)
            logging.info("Temporary directory cleaned up due to exception.")
        return sourceCodeStored

    logging.info(
        "outside 'secure_temp_repo_dir' in locals() => %s",
        ("secure_temp_repo_dir" in locals()),
    )
    logging.info("outside os.path.exists => %s", os.path.exists(secure_temp_repo_dir))
    if "secure_temp_repo_dir" in locals() and os.path.exists(secure_temp_repo_dir):
        for entry in os.listdir(secure_temp_repo_dir):
            logging.info(entry)
        # shutil.rmtree(secure_temp_repo_dir)
        # logging.info("Temporary directory cleaned up outside.")

    sourceCodeStored = True
    tool_context.state["secure_temp_repo_dir"] = secure_temp_repo_dir

    return sourceCodeStored


# FOR TESTING
# if __name__ == "__main__":
#     fetch_source_code_from_git_repo("https://github.com/cbangera-google/otel-agent.git", "ACCESS_TOKEN")
