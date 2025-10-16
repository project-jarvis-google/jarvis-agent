import os
import subprocess
import json
import logging

from app.utils.pandas_utils import list_of_dict_to_md_table
from google.adk.tools import ToolContext

from app.sub_agents.tech_stack_profiler_agent.utils.json_utils import (
    filter_json_arr,
    extract_json_arr_str,
)
from .prompt import FRAMEWORK_IDENTIFICATION_GEMINI_PROMPT


def identify_frameworks(tool_context: ToolContext) -> bool:
    # tool_context.state["filtered_framework_data"] = "filtered_framework_sample_data"

    # return True

    is_framework_identification_successful = False

    secure_temp_repo_dir = tool_context.state["secure_temp_repo_dir"]

    logging.info(
        "inside identify_frameworks secure_temp_repo_dir => %s", secure_temp_repo_dir
    )

    logging.info(
        "in identify_frameworks 'secure_temp_repo_dir' in locals() => %s",
        ("secure_temp_repo_dir" in locals()),
    )
    logging.info(
        "in identify_frameworks os.path.exists => %s",
        os.path.exists(secure_temp_repo_dir),
    )
    for entry in os.listdir(secure_temp_repo_dir):
        logging.info(entry)
    if "secure_temp_repo_dir" in locals() and os.path.exists(secure_temp_repo_dir):
        frameworks_json_str = []

        try:
            is_mock_enabled = os.getenv(
                "ENABLE_FRAMEWORK_IDENTIFICATION_MOCK_DATA", "False"
            )
            if is_mock_enabled == "True":
                logging.info("is_mock_enabled => %s", is_mock_enabled)
                stdout = """
                ```json
                [
                {
                    "name": "Spring Boot",
                    "category": "Application Framework",
                    "evidence": "Identified parent dependency 'spring-boot-starter-parent' and multiple 'spring-boot-starter-*' dependencies in Account-Service/pom.xml."
                },
                {
                    "name": "Spring Cloud",
                    "category": "Microservice Framework",
                    "evidence": "Identified 'spring-cloud-dependencies' and starters like 'spring-cloud-starter-netflix-eureka-client' in Account-Service/pom.xml and 'spring-cloud-starter-gateway' in API-Gateway/pom.xml."
                },
                {
                    "name": "Maven",
                    "category": "Build Automation Tool",
                    "evidence": "Identified 'pom.xml' file in the root of multiple service directories, such as Account-Service/pom.xml."
                },
                {
                    "name": "Docker",
                    "category": "Deployment / IaC Tool",
                    "evidence": "Identified a 'Dockerfile' in the User-Service directory."
                },
                {
                    "name": "Spring Data JPA",
                    "category": "Database / ORM",
                    "evidence": "Identified 'spring-boot-starter-data-jpa' as a dependency in Account-Service/pom.xml."
                },
                {
                    "name": "JUnit",
                    "category": "Testing Framework",
                    "evidence": "Inferred from the 'spring-boot-starter-test' dependency in Account-Service/pom.xml, which includes JUnit by default."
                },
                {
                    "name": "Mockito",
                    "category": "Testing Framework",
                    "evidence": "Inferred from the 'spring-boot-starter-test' dependency in Account-Service/pom.xml, which includes Mockito by default."
                },
                {
                    "name": "Spring Security",
                    "category": "Security Framework",
                    "evidence": "Identified 'spring-boot-starter-oauth2-resource-server' as a dependency in API-Gateway/pom.xml."
                }
                ]
                ```
                """
                stderr = """

                """

            else:
                gemini_env = os.environ.copy()
                gemini_env["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY")
                args = "-p " + '"' + FRAMEWORK_IDENTIFICATION_GEMINI_PROMPT + '"'
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

            frameworks_json_str = extract_json_arr_str(stdout)
            is_framework_identification_successful = True

            # tool_context.state["frameworks_json_str"] = frameworks_json_str

            frameworks_json = json.loads(frameworks_json_str)
            desired_frameworks_attributes = ["name", "category"]

            filtered_framework_data = filter_json_arr(
                frameworks_json, desired_frameworks_attributes
            )

            filtered_framework_data_final_str = "\n".join(
                [
                    " - ".join(map(str, inner_list))
                    for inner_list in filtered_framework_data
                ]
            )

            tool_context.state["filtered_framework_data_final_str"] = (
                filtered_framework_data_final_str
            )

            # tool_context.state["filtered_framework_data"] = filtered_framework_data

            # tool_context.state["filtered_framework_data_md_table"] = list_of_dict_to_md_table(
            #     filtered_framework_data, 50
            # )

            for entry in os.listdir(secure_temp_repo_dir):
                logging.info(entry)
            # shutil.rmtree(secure_temp_repo_dir)
            # logging.info("Temporary directory cleaned up in identify_frameworks.")
        except subprocess.CalledProcessError as e:
            logging.error("CalledProcessError Exception encountered !!!")
            logging.error("Error occurred: %s", e)
            logging.error("Error output (stderr): %s", e.stderr)
            logging.error("Command that failed: %s", e.cmd)
            logging.error("Return code: %s", e.returncode)
            return is_framework_identification_successful
        except subprocess.TimeoutExpired as e:
            logging.error("TimeoutExpired Exception encountered !!!")
            logging.error("Error occurred: %s", e)
            logging.error("Error output (stdout): %s", e.stdout)
            logging.error("Error output (stderr): %s", e.stderr)
            logging.error("Command that failed: %s", e.cmd)
            return is_framework_identification_successful

    return is_framework_identification_successful
