import json
import logging
import os
import subprocess

from google.adk.tools import ToolContext

from app.sub_agents.tech_stack_profiler_agent.utils.json_utils import filter_json_arr

# TODO: Error Handling


def identify_languages_from_source_code(tool_context: ToolContext) -> bool:
    secure_temp_repo_dir = tool_context.state["secure_temp_repo_dir"]

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
                "ENRY_INSTALLATION_LOCATION", "/go-installs/enry"
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
        desired_languages_attributes = ["language", "percentage"]

        filtered_language_data = filter_json_arr(
            languages_breakdown_json, desired_languages_attributes
        )

        filtered_language_data_final_str = "\n".join(
            [" - ".join(map(str, inner_list)) for inner_list in filtered_language_data]
        )

        tool_context.state["filtered_language_data_final_str"] = (
            filtered_language_data_final_str
        )

        # tool_context.state["filtered_language_data"] = filtered_language_data

        # tool_context.state["filtered_language_data_md_table"] = list_of_dict_to_md_table(filtered_language_data, 50)

        for entry in os.listdir(secure_temp_repo_dir):
            logging.info(entry)
        # shutil.rmtree(secure_temp_repo_dir)
        # logging.info("Temporary directory cleaned up in identify_languages_from_source_code.")

    return True


# FOR TESTING
# if __name__ == "__main__":
#     fetch_source_code_from_git_repo("https://github.com/cbangera-google/otel-agent.git", "ACCESS_TOKEN")
