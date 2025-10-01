import asyncio
import concurrent.futures
import os
import shutil

import subprocess

from app.utils.pandas_utils import list_of_dict_to_md_table
from google.adk.tools import ToolContext

import json

from app.sub_agents.tech_stack_profiler_agent.utils.json_utils import filter_json_arr

import logging

#TODO: Error Handling

def identify_languages_from_source_code(secure_temp_repo_dir: str) -> str:

    # secure_temp_repo_dir = tool_context.state["secure_temp_repo_dir"]

    filtered_language_data_final_str = ""
    
    logging.info("secure_temp_repo_dir => %s", secure_temp_repo_dir)

    logging.info("in identify_languages_from_source_code 'secure_temp_repo_dir' in locals() => %s", ('secure_temp_repo_dir' in locals()))
    logging.info("in identify_languages_from_source_code os.path.exists => %s", os.path.exists(secure_temp_repo_dir))
    if 'secure_temp_repo_dir' in locals() and os.path.exists(secure_temp_repo_dir):

        is_mock_enabled = os.getenv("ENABLE_LANGUAGE_IDENTIFICATION_MOCK_DATA", "False")
        if is_mock_enabled == "True":
            logging.info("is_mock_enabled => %s", is_mock_enabled)
            stdout = '''
            [{"color":"#b07219","language":"Java","percentage":"99.89%","type":"unknown"},{"color":"#384d54","language":"Dockerfile","percentage":"0.11%","type":"unknown"}]
            '''
            stderr = '''

            '''

        else:
            # result = subprocess.run(["/usr/local/google/home/cbangera/go/bin/enry","-json"], cwd=secure_temp_repo_dir, capture_output=True, text=True, check=True)
            # stderr = result.stderr
            # stdout = result.stdout
            with subprocess.Popen(["/usr/local/google/home/cbangera/go/bin/enry", "-json"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=secure_temp_repo_dir,
                text=True
            ) as process:
                stdout, stderr = process.communicate(timeout=120)

        logging.info("result.stderr => %s", stderr)
        logging.info("result.stdout => %s", stdout)

        # tool_context.state["languages_breakdown_json_str"] = stdout

        languages_breakdown_json = json.loads(stdout)
        desired_languages_attributes = ["language", "percentage"]

        filtered_language_data = filter_json_arr(languages_breakdown_json, desired_languages_attributes)

        filtered_language_data_final_str = '\n'.join([' - '.join(map(str, inner_list)) for inner_list in filtered_language_data])

        # tool_context.state["filtered_language_data_final_str"] = filtered_language_data_final_str


        # tool_context.state["filtered_language_data"] = filtered_language_data

        # tool_context.state["filtered_language_data_md_table"] = list_of_dict_to_md_table(filtered_language_data, 50)
        
        for entry in os.listdir(secure_temp_repo_dir):
            logging.info(entry)
        # shutil.rmtree(secure_temp_repo_dir)
        # logging.info("Temporary directory cleaned up in identify_languages_from_source_code.")

    return filtered_language_data_final_str


async def identify_languages_from_source_code_initiator(tool_context: ToolContext) -> bool:
    secure_temp_repo_dir = tool_context.state["secure_temp_repo_dir"]
    loop = asyncio.get_running_loop()
    with concurrent.futures.ProcessPoolExecutor() as pool:
        tool_context.state["filtered_language_data_final_str"] = await loop.run_in_executor(pool, identify_languages_from_source_code, secure_temp_repo_dir)
        return True

#FOR TESTING
# if __name__ == "__main__":
#     fetch_source_code_from_git_repo("https://github.com/cbangera-google/otel-agent.git", "ACCESS_TOKEN")