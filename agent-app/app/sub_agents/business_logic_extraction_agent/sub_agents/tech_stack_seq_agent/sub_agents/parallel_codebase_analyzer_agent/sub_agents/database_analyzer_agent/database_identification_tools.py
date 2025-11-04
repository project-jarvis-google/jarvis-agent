import json
import logging
import os
import subprocess
from typing import Any

from google.adk.tools import ToolContext

from app.sub_agents.tech_stack_profiler_agent.utils.json_utils import (
    extract_json_arr_str,
    filter_json_arr,
)

from .prompt import DATABASE_IDENTIFICATION_GEMINI_PROMPT


def identify_databases(tool_context: ToolContext) -> bool:
    # tool_context.state["filtered_database_data"] = "filtered_database_sample_data"

    # return True

    is_database_identification_successful = False

    secure_temp_repo_dir = tool_context.state["secure_temp_repo_dir"]

    logging.info(
        "inside identify_databases secure_temp_repo_dir => %s", secure_temp_repo_dir
    )

    logging.info(
        "in identify_databases 'secure_temp_repo_dir' in locals() => %s",
        ("secure_temp_repo_dir" in locals()),
    )
    logging.info(
        "in identify_databases os.path.exists => %s",
        os.path.exists(secure_temp_repo_dir),
    )
    for entry in os.listdir(secure_temp_repo_dir):
        logging.info(entry)
    if "secure_temp_repo_dir" in locals() and os.path.exists(secure_temp_repo_dir):
        databases_json_str: str = "[]"

        try:
            is_mock_enabled = os.getenv(
                "ENABLE_DATABASE_IDENTIFICATION_MOCK_DATA", "False"
            )
            if is_mock_enabled == "True":
                logging.info("is_mock_enabled => %s", is_mock_enabled)
                stdout = """
                ```json
                [
                {
                    "name": "MySQL",
                    "evidence": "Identified as a dependency in Account-Service/pom.xml",
                    "configurations": [
                    "Connection String: spring.datasource.url=jdbc:mysql://localhost:3306/account_service found in Account-Service/src/main/resources/application.yml",
                    "Username: spring.datasource.username=root found in Account-Service/src/main/resources/application.yml",
                    "Password: spring.datasource.password=root found in Account-Service/src/main/resources/application.yml"
                    ]
                },
                {
                    "name": "MySQL",
                    "evidence": "Identified as a dependency in Fund-Transfer/pom.xml",
                    "configurations": [
                    "Connection String: spring.datasource.url=jdbc:mysql://localhost:3306/fund_transfer_service found in Fund-Transfer/src/main/resources/application.yml",
                    "Username: spring.datasource.username=root found in Fund-Transfer/src/main/resources/application.yml",
                    "Password: spring.datasource.password=root found in Fund-Transfer/src/main/resources/application.yml"
                    ]
                },
                {
                    "name": "MySQL",
                    "evidence": "Identified as a dependency in Sequence-Generator/pom.xml",
                    "configurations": [
                    "Connection String: spring.datasource.url=jdbc:mysql://localhost:3306/sequence_generator found in Sequence-Generator/src/main/resources/application.yml",
                    "Username: spring.datasource.username=root found in Sequence-Generator/src/main/resources/application.yml",
                    "Password: spring.datasource.password=root found in Sequence-Generator/src/main/resources/application.yml"
                    ]
                },
                {
                    "name": "MySQL",
                    "evidence": "Identified as a dependency in Transaction-Service/pom.xml",
                    "configurations": [
                    "Connection String: spring.datasource.url=jdbc:mysql://localhost:3306/transaction_service found in Transaction-Service/src/main/resources/application.yml",
                    "Username: spring.datasource.username=root found in Transaction-Service/src/main/resources/application.yml",
                    "Password: spring.datasource.password=root found in Transaction-Service/src/main/resources/application.yml"
                    ]
                },
                {
                    "name": "MySQL",
                    "evidence": "Identified as a dependency in User-Service/pom.xml",
                    "configurations": [
                    "Connection String: spring.datasource.url=jdbc:mysql://${MYSQL_HOST:localhost}:${MYSQL_PORT:3306}/${MYSQL_DB_NAME:user_service} found in User-Service/src/main/resources/application.yml",
                    "Username: spring.datasource.username=${MYSQL_USER:root} found in User-Service/src/main/resources/application.yml",
                    "Password: spring.datasource.password=${MYSQL_PASSWORD:root} found in User-Service/src/main/resources/application.yml"
                    ]
                }
                ]
                ```
                """
                stderr = """

                """

            else:
                gemini_env = os.environ.copy()
                gemini_env["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY", "")
                args = "-p " + '"' + DATABASE_IDENTIFICATION_GEMINI_PROMPT + '"'
                result = subprocess.run(
                    ["/usr/local/bin/gemini", args],
                    timeout=120,
                    env=gemini_env,
                    cwd=secure_temp_repo_dir,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                stderr = result.stderr
                stdout = result.stdout

            logging.info("result.stderr => %s", stderr)
            logging.info("result.stdout => %s", stdout)

            extracted_json = extract_json_arr_str(stdout)
            if extracted_json:
                databases_json_str = extracted_json

            is_database_identification_successful = True

            # tool_context.state["databases_json_str"] = databases_json_str

            databases_json: list[Any] = json.loads(databases_json_str)
            desired_databases_attributes = ["name", "configurations"]

            filtered_database_data = filter_json_arr(
                databases_json, desired_databases_attributes
            )

            filtered_database_data_final_str = "\n\n".join(
                [
                    "\n".join(map(str, inner_list))
                    for inner_list in filtered_database_data
                ]
            )

            tool_context.state["filtered_database_data_final_str"] = (
                filtered_database_data_final_str
            )

            # tool_context.state["filtered_database_data"] = filtered_database_data

            # tool_context.state["filtered_database_data_md_table"] = list_of_dict_to_md_table(filtered_database_data, 50)

            for entry in os.listdir(secure_temp_repo_dir):
                logging.info(entry)
            # shutil.rmtree(secure_temp_repo_dir)
            # logging.info("Temporary directory cleaned up in identify_databases.")
        except subprocess.CalledProcessError as e:
            logging.error("CalledProcessError Exception encountered !!!")
            logging.error("Error occurred: %s", e)
            logging.error("Error output (stderr): %s", e.stderr)
            logging.error("Command that failed: %s", e.cmd)
            logging.error("Return code: %s", e.returncode)
            return is_database_identification_successful
        except subprocess.TimeoutExpired as e:
            logging.error("TimeoutExpired Exception encountered !!!")
            logging.error("Error occurred: %s", e)
            logging.error("Error output (stdout): %s", e.stdout)
            logging.error("Error output (stderr): %s", e.stderr)
            logging.error("Command that failed: %s", e.cmd)
            return is_database_identification_successful

    return is_database_identification_successful
