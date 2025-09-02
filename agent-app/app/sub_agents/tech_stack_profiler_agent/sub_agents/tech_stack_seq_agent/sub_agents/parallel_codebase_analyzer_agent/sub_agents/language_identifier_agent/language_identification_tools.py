import os
import shutil

import subprocess

from google.adk.tools import ToolContext

import json

from app.sub_agents.tech_stack_profiler_agent.utils.json_utils import filter_json_arr

import logging

#TODO: Error Handling

def identify_languages_from_source_code(tool_context: ToolContext) -> bool:

    secure_temp_repo_dir = tool_context.state["secure_temp_repo_dir"]
    
    logging.info("secure_temp_repo_dir => %s", secure_temp_repo_dir)

    logging.info("in identify_languages_from_source_code 'secure_temp_repo_dir' in locals() => %s", ('secure_temp_repo_dir' in locals()))
    logging.info("in identify_languages_from_source_code os.path.exists => %s", os.path.exists(secure_temp_repo_dir))
    if 'secure_temp_repo_dir' in locals() and os.path.exists(secure_temp_repo_dir):
        
        result = subprocess.run(["/go-installs/enry","-json"], cwd=secure_temp_repo_dir, capture_output=True, text=True, check=True)

        tool_context.state["languages_breakdown_json_str"] = result.stdout

        languages_breakdown_json = json.loads(result.stdout)
        desired_languages_attributes = ["language", "percentage"]

        filtered_language_data = filter_json_arr(languages_breakdown_json, desired_languages_attributes)

        tool_context.state["filtered_language_data"] = filtered_language_data
        
        for entry in os.listdir(secure_temp_repo_dir):
            logging.info(entry)
        # shutil.rmtree(secure_temp_repo_dir)
        # logging.info("Temporary directory cleaned up in identify_languages_from_source_code.")

    return True

#FOR TESTING
# if __name__ == "__main__":
#     fetch_source_code_from_git_repo("https://github.com/cbangera-google/otel-agent.git", "ACCESS_TOKEN")