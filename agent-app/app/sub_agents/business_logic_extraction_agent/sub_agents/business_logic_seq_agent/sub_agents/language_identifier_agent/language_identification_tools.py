import json
import logging
import os
import subprocess

from google.adk.tools import ToolContext
from pydantic import BaseModel

from app.sub_agents.tech_stack_profiler_agent.utils.json_utils import filter_json_arr

# TODO: Error Handling

class LanguageIdentificationResult(BaseModel):
    is_supported: bool
    found_languages: str

def identify_languages_from_source_code(tool_context: ToolContext) -> dict:
    secure_temp_repo_dir = tool_context.state["secure_temp_repo_dir"]
    # secure_temp_repo_dir = "/Users/manojmj/Documents/temp"

    logging.info("secure_temp_repo_dir => %s", secure_temp_repo_dir)

    logging.info(
        "in identify_languages_from_source_code 'secure_temp_repo_dir' in locals() => %s",
        ("secure_temp_repo_dir" in locals()),
    )
    logging.info(
        "in identify_languages_from_source_code os.path.exists => %s",
        os.path.exists(secure_temp_repo_dir),
    )
    if "secure_temp_repo_dir" in locals() and os.path.exists(secure_temp_repo_dir):
        is_mock_enabled = os.getenv("ENABLE_LANGUAGE_IDENTIFICATION_MOCK_DATA", "False")
        if is_mock_enabled == "True":
            logging.info("is_mock_enabled => %s", is_mock_enabled)
            stdout = """
            [{"color":"#b07219","language":"Java","percentage":"99.89%","type":"unknown"},{"color":"#384d54","language":"Dockerfile","percentage":"0.11%","type":"unknown"}]
            """
            stderr = """

            """

        else:
            enry_install_location = os.getenv(
                "ENRY_INSTALLATION_LOCATION", "/Users/manojmj/Documents/google/internalproject/jarvis-agent/enry/enry"
            )
            result = subprocess.run(
                [enry_install_location, "-json"],
                cwd=secure_temp_repo_dir,
                capture_output=True,
                text=True,
                check=True,
            )
            stderr = result.stderr
            stdout = result.stdout

        logging.info("result.stderr => %s", stderr)
        logging.info("result.stdout => %s", stdout)

        # tool_context.state["languages_breakdown_json_str"] = stdout

        languages_breakdown_json = json.loads(stdout)

        # Sort by percentage descending
        languages_breakdown_json.sort(key=lambda x: float(x["percentage"].strip("%")), reverse=True)

        # Format Top 4 for the agent to display
        top_4_languages = languages_breakdown_json[:4]
        filtered_language_data_final_str = "\n".join(
            [f"{lang.get('language', 'Unknown')}: {lang.get('percentage', '0%')}" for lang in top_4_languages]
        )

        tool_context.state["filtered_language_data_final_str"] = (
            filtered_language_data_final_str
        )

        is_supported = True
        if languages_breakdown_json:
            required_languages = tool_context.state.get("required_languages", ["Java", "C#", "SQL", "PL/SQL", "T-SQL"])
            top_4_languages_list = [x["language"] for x in languages_breakdown_json[:4]]
            if required_languages and not any(lang in required_languages for lang in top_4_languages_list):
                logging.info(f"No required language found in top 4: {top_4_languages_list}. Required: {required_languages}. Exiting.")
                is_supported = False

        # tool_context.state["filtered_language_data"] = filtered_language_data

        # tool_context.state["filtered_language_data_md_table"] = list_of_dict_to_md_table(filtered_language_data, 50)

        for entry in os.listdir(secure_temp_repo_dir):
            logging.info(entry)
        # shutil.rmtree(secure_temp_repo_dir)
        # logging.info("Temporary directory cleaned up in identify_languages_from_source_code.")

        return LanguageIdentificationResult(
            is_supported=is_supported, found_languages=filtered_language_data_final_str
        ).dict()

    return LanguageIdentificationResult(
        is_supported=False, found_languages="Source code directory not found."
    ).dict()


# FOR TESTING
# if __name__ == "__main__":
#     fetch_source_code_from_git_repo("https://github.com/cbangera-google/otel-agent.git", "ACCESS_TOKEN")
