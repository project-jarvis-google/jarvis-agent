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

from .prompt import CODEBASE_ANALYZER_GEMINI_PROMPT


def identify_technical_aspects(tool_context: ToolContext) -> bool:
    # tool_context.state["filtered_framework_data"] = "filtered_framework_sample_data"

    # return True

    is_analysis_successful = False

    secure_temp_repo_dir = tool_context.state["secure_temp_repo_dir"]

    logging.info(
        "inside identify_technical_aspects secure_temp_repo_dir => %s",
        secure_temp_repo_dir,
    )

    logging.info(
        "in identify_technical_aspects 'secure_temp_repo_dir' in locals() => %s",
        ("secure_temp_repo_dir" in locals()),
    )
    logging.info(
        "in identify_technical_aspects os.path.exists => %s",
        os.path.exists(secure_temp_repo_dir),
    )
    for entry in os.listdir(secure_temp_repo_dir):
        logging.info(entry)
    if "secure_temp_repo_dir" in locals() and os.path.exists(secure_temp_repo_dir):
        frameworks_json_str: str = "[]"

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
                gemini_env["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY", "")
                args = "-p " + '"' + CODEBASE_ANALYZER_GEMINI_PROMPT + '"'
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

            filtered_framework_data_final_str = filter_and_format_data(stdout)

            is_analysis_successful = True

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
            # logging.info("Temporary directory cleaned up in identify_technical_aspects.")
        except subprocess.CalledProcessError as e:
            logging.error("CalledProcessError Exception encountered !!!")
            logging.error("Error occurred: %s", e)
            logging.error("Error output (stderr): %s", e.stderr)
            logging.error("Command that failed: %s", e.cmd)
            logging.error("Return code: %s", e.returncode)
            return is_analysis_successful
        except subprocess.TimeoutExpired as e:
            logging.error("TimeoutExpired Exception encountered !!!")
            logging.error("Error occurred: %s", e)
            logging.error("Error output (stdout): %s", e.stdout)
            logging.error("Error output (stderr): %s", e.stderr)
            logging.error("Command that failed: %s", e.cmd)
            return is_analysis_successful

    return is_analysis_successful


def filter_and_format_data(stdout: str) -> str:
    filtered_framework_data_final_str = "NO DATA FOUND"

    try:
        extracted_json = extract_json_arr_str(stdout)
        if extracted_json:
            frameworks_json_str = extracted_json

        # tool_context.state["frameworks_json_str"] = frameworks_json_str

        frameworks_json: list[Any] = json.loads(frameworks_json_str)
        desired_frameworks_attributes = ["name", "category", "version", "description"]

        filtered_framework_data = filter_json_arr(
            frameworks_json, desired_frameworks_attributes
        )

        logging.info("filtered_framework_data => %s", filtered_framework_data)

        formatted_blocks = []
        for item in filtered_framework_data:
            name, category, version, description = item
            formatted_blocks.append(
                f"####{name}\nCATEGORY: {category}\nDESCRIPTION: {description}\nVERSION: {version}"
            )
        filtered_framework_data_final_str = "\n\n".join(formatted_blocks)
    except Exception as e:
        logging.error(f"Exception encountered !!! {e}")

    return filtered_framework_data_final_str


if __name__ == "__main__":
    str = filter_and_format_data("""
    ```json
    [
    {
        "name": "Spring Boot",
        "category": "Application Framework",
        "version": "2.7.15",
        "description": "An open-source Java-based framework used to create a micro Service.",
        "evidence": "Identified as a parent dependency in multiple pom.xml files."
    },
    {
        "name": "Spring Cloud",
        "category": "Microservices Framework",
        "version": "2021.0.8",
        "description": "Provides tools for developers to quickly build some of the common patterns in distributed systems.",
        "evidence": "Identified as a dependency in multiple pom.xml files."
    },
    {
        "name": "Spring Cloud Gateway",
        "category": "API Gateway",
        "version": "2021.0.8",
        "description": "Provides a simple, yet effective way to route to APIs and provide cross-cutting concerns to them such as security, monitoring/metrics, and resiliency.",
        "evidence": "Identified as a dependency in API-Gateway/pom.xml."
    },
    {
        "name": "Spring Cloud Netflix Eureka",
        "category": "Service Discovery",
        "version": "2021.0.8",
        "description": "A REST (Representational State Transfer) based service that is primarily used in the AWS cloud for locating services for the purpose of load balancing and failover of middle-tier servers.",
        "evidence": "Identified as a dependency in multiple pom.xml files."
    },
    {
        "name": "Spring Cloud OpenFeign",
        "category": "Declarative REST Client",
        "version": "2021.0.8",
        "description": "A declarative REST client for Spring Boot applications.",
        "evidence": "Identified as a dependency in multiple pom.xml files."
    },
    {
        "name": "Spring Boot Actuator",
        "category": "Monitoring and Management",
        "version": "2.7.15",
        "description": "Enables production-ready features for a Spring Boot application, such as monitoring and metrics.",
        "evidence": "Identified as a dependency in multiple pom.xml files."
    },
    {
        "name": "Spring Data JPA",
        "category": "Data Access Framework",
        "version": "2.7.15",
        "description": "Simplifies the creation of JPA-based data access layers.",
        "evidence": "Identified as a dependency in multiple pom.xml files."
    },
    {
        "name": "Spring Web",
        "category": "Web Framework",
        "version": "2.7.15",
        "description": "Provides features for building web applications, including a web server and RESTful services.",
        "evidence": "Identified as a dependency in multiple pom.xml files."
    },
    {
        "name": "Spring Boot Test",
        "category": "Testing Framework",
        "version": "2.7.15",
        "description": "Provides testing support for Spring Boot applications.",
        "evidence": "Identified as a dependency in multiple pom.xml files."
    },
    {
        "name": "Spring Boot Validation",
        "category": "Data Validation",
        "version": "2.7.15",
        "description": "Provides support for data validation using Hibernate Validator.",
        "evidence": "Identified as a dependency in multiple pom.xml files."
    },
    {
        "name": "Spring Boot DevTools",
        "category": "Development Tool",
        "version": "2.7.15",
        "description": "Provides development-time features like automatic restarts and live reload.",
        "evidence": "Identified as a dependency in multiple pom.xml files."
    },
    {
        "name": "MySQL Connector/J",
        "category": "Database Driver",
        "version": "Not specified",
        "description": "JDBC driver for MySQL.",
        "evidence": "Identified as a dependency in multiple pom.xml files."
    },
    {
        "name": "Lombok",
        "category": "Boilerplate-reducing Library",
        "version": "Not specified",
        "description": "A Java library that automatically plugs into your editor and build tools to reduce boilerplate code.",
        "evidence": "Identified as a dependency in multiple pom.xml files."
    },
    {
        "name": "Maven",
        "category": "Build Automation Tool",
        "version": "Not specified",
        "description": "A build automation tool used primarily for Java projects.",
        "evidence": "Identified by the presence of pom.xml files."
    },
    {
        "name": "Keycloak Admin Client",
        "category": "Identity and Access Management",
        "version": "21.0.1",
        "description": "A client library for managing Keycloak.",
        "evidence": "Identified as a dependency in User-Service/pom.xml."
    },
    {
        "name": "ModelMapper",
        "category": "Object Mapping Library",
        "version": "3.1.1",
        "description": "An intelligent object mapping library.",
        "evidence": "Identified as a dependency in User-Service/pom.xml."
    },
    {
        "name": "Spring Security OAuth2 Client",
        "category": "Security Framework",
        "version": "2.7.14",
        "description": "Provides OAuth 2.0 client support for Spring Boot applications.",
        "evidence": "Identified as a dependency in API-Gateway/pom.xml."
    },
    {
        "name": "Spring Security OAuth2 Resource Server",
        "category": "Security Framework",
        "version": "2.7.14",
        "description": "Provides OAuth 2.0 resource server support for Spring Boot applications.",
        "evidence": "Identified as a dependency in API-Gateway/pom.xml."
    },
    {
        "name": "Docker",
        "category": "Deployment / IaC Tool",
        "version": "Not specified",
        "description": "A platform for developing, shipping, and running applications in containers.",
        "evidence": "Identified by the presence of a Dockerfile in the User-Service directory."
    },
    {
        "name": "OpenJDK",
        "category": "Java Development Kit",
        "version": "17",
        "description": "An open-source implementation of the Java Platform, Standard Edition.",
        "evidence": "Identified by the 'FROM openjdk:17-jdk' instruction in the User-Service/Dockerfile."
    }
    ]
    ```
    """)
    logging.info(f"filter and format str => {str}")
