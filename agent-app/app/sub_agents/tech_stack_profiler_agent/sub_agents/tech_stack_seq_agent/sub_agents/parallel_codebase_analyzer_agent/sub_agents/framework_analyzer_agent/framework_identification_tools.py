import os
import subprocess
import json
import logging

from google.adk.tools import ToolContext

from app.sub_agents.tech_stack_profiler_agent.utils.json_utils import filter_json_arr, extract_json_arr_str
from .prompt import FRAMEWORK_IDENTIFICATION_GEMINI_PROMPT

def identify_frameworks(tool_context: ToolContext) -> bool:

    is_framework_identification_successful = False

    secure_temp_repo_dir = tool_context.state["secure_temp_repo_dir"]

    logging.info("inside identify_frameworks secure_temp_repo_dir => %s", secure_temp_repo_dir)

    logging.info("in identify_frameworks 'secure_temp_repo_dir' in locals() => %s", ('secure_temp_repo_dir' in locals()))
    logging.info("in identify_frameworks os.path.exists => %s", os.path.exists(secure_temp_repo_dir))
    for entry in os.listdir(secure_temp_repo_dir):
        logging.info(entry)
    if 'secure_temp_repo_dir' in locals() and os.path.exists(secure_temp_repo_dir):
        frameworks_json_str = []

        try:
            gemini_env = os.environ.copy()  
            gemini_env["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY")
            args = "-p " + "\"" + FRAMEWORK_IDENTIFICATION_GEMINI_PROMPT + "\""
            result = subprocess.run(["/usr/local/bin/gemini", args], timeout=120, env=gemini_env, cwd=secure_temp_repo_dir, capture_output=True, text=True, check=True)
            logging.info("result.stderr => %s", result.stderr)
            logging.info("result.stdout => %s", result.stdout)

            frameworks_json_str = extract_json_arr_str(result.stdout)
            is_framework_identification_successful = True

            tool_context.state["frameworks_json_str"] = frameworks_json_str

            frameworks_json = json.loads(frameworks_json_str)
            desired_frameworks_attributes = ["name", "category"]
            
            filtered_framework_data = filter_json_arr(frameworks_json, desired_frameworks_attributes)

            tool_context.state["filtered_framework_data"] = filtered_framework_data

            for entry in os.listdir(secure_temp_repo_dir):
                logging.info(entry)
            # shutil.rmtree(secure_temp_repo_dir)
            # logging.info("Temporary directory cleaned up in identify_frameworks.")
        except subprocess.CalledProcessError as e:
            logging.error("CalledProcessError Exception encountered !!!")
            logging.error(f"Error occurred: {e}")
            logging.error(f"Error output (stderr): {e.stderr}")
            logging.error(f"Command that failed: {e.cmd}")
            logging.error(f"Return code: {e.returncode}")
            return is_framework_identification_successful
        except subprocess.TimeoutExpired as e:
            logging.error("TimeoutExpired Exception encountered !!!")
            logging.error(f"Error occurred: {e}")
            logging.error(f"Error output (stdout): {e.stdout}")
            logging.error(f"Error output (stderr): {e.stderr}")
            logging.error(f"Command that failed: {e.cmd}")
            return is_framework_identification_successful

    return is_framework_identification_successful

#FOR TESTING
# if __name__ == "__main__":
#     logging.info(identify_frameworks("/usr/local/google/home/cbangera/Projects/OtelAgent/otel-agent-gemini-cli-test"))