import json
import logging
import os
import subprocess
from collections import defaultdict

from google.adk.tools import ToolContext

from app.sub_agents.tech_stack_profiler_agent.utils.json_utils import filter_json_arr

# TODO: Error Handling

def detect_sql_dialect(file_path):
    """
    Detects the dialect of a SQL file (T-SQL or PL/SQL) based on keywords.
    """
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read().upper()

    # Heuristics for T-SQL (Microsoft SQL Server)
    tsql_keywords = ['SELECT @@VERSION', 'SP_', 'CREATE PROCEDURE', 'BEGIN TRY', 'MERGE']
    if any(keyword in content for keyword in tsql_keywords):
        return "T-SQL"

    # Heuristics for PL/SQL (Oracle)
    plsql_keywords = ['DECLARE', 'BEGIN', 'EXCEPTION', 'DBMS_OUTPUT.PUT_LINE', 'CREATE OR REPLACE PROCEDURE']
    if any(keyword in content for keyword in plsql_keywords):
        return "PL/SQL"

    return "SQL" # Default to generic SQL

from typing import Optional

def identify_languages_from_source_code(tool_context: ToolContext, scope: Optional[str] = None) -> bool:
    secure_temp_repo_dir = tool_context.state["secure_temp_repo_dir"]
    logging.info("secure_temp_repo_dir => %s", secure_temp_repo_dir)

    if not os.path.exists(secure_temp_repo_dir):
        logging.error("Secure temp repo directory not found.")
        return False

    try:
        enry_install_location = os.getenv("ENRY_INSTALLATION_LOCATION", "/go-installs/enry")
        command = [enry_install_location, "-json", "-breakdown"]
        if scope:
            logging.info("Analyzing scope: %s", scope)
            command.append(scope)
        
        result = subprocess.run(
            command,
            cwd=secure_temp_repo_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        
        languages_breakdown_json = json.loads(result.stdout)
        
        # Refine SQL dialects
        if "SQL" in languages_breakdown_json:
            sql_files = languages_breakdown_json["SQL"]
            del languages_breakdown_json["SQL"]
            
            sql_dialects = defaultdict(list)
            for sql_file in sql_files:
                dialect = detect_sql_dialect(os.path.join(secure_temp_repo_dir, sql_file))
                sql_dialects[dialect].append(sql_file)
            
            languages_breakdown_json.update(sql_dialects)

        # Calculate percentages
        total_files = sum(len(files) for files in languages_breakdown_json.values())
        language_percentages = {
            lang: (len(files) / total_files) * 100
            for lang, files in languages_breakdown_json.items()
        }

        # Find unsupported files
        all_files = set()
        for root, _, files in os.walk(secure_temp_repo_dir):
            for file in files:
                all_files.add(os.path.relpath(os.path.join(root, file), secure_temp_repo_dir))

        processed_files = set()
        for files in languages_breakdown_json.values():
            processed_files.update(files)
            
        unsupported_files = list(all_files - processed_files)

        # Prepare final output
        final_breakdown = [
            {"language": lang, "percentage": f"{percentage:.2f}%"}
            for lang, percentage in language_percentages.items()
        ]

        tool_context.state["languages_breakdown"] = final_breakdown
        tool_context.state["unsupported_files"] = unsupported_files
        
        logging.info("Language identification successful.")
        logging.info("Languages breakdown: %s", final_breakdown)
        logging.info("Unsupported files: %s", unsupported_files)

        # Regarding syntax error detection (AC 1.4):
        # Detecting syntax errors requires a full parser for each language, which is beyond the
        # capabilities of the current language identification tool (enry).
        # I recommend skipping this requirement for now.
        tool_context.state["syntax_error_detection_note"] = "Detecting syntax errors is not supported in this version."


    except subprocess.CalledProcessError as e:
        logging.error("Enry process failed: %s", e.stderr)
        return False
    except json.JSONDecodeError as e:
        logging.error("Failed to parse enry output: %s", e)
        return False
    except Exception as e:
        logging.error("An unexpected error occurred: %s", e)
        return False

    return True
