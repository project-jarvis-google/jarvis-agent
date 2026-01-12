import json
import logging
import os
import re
from typing import Any

import google.auth
import mysql.connector
from google import genai
from google.api_core import exceptions
from google.genai import types

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

try:
    _, project_id = google.auth.default()
    GOOGLE_CLOUD_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", project_id)
except google.auth.exceptions.DefaultCredentialsError:
    GOOGLE_CLOUD_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT")  # type: ignore[assignment]

if not GOOGLE_CLOUD_PROJECT:
    logger.warning(
        "GOOGLE_CLOUD_PROJECT not set in environment or Application Default Credentials."
    )

GOOGLE_CLOUD_LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
GOOGLE_GENAI_USE_VERTEXAI = os.environ.get(
    "GOOGLE_GENAI_USE_VERTEXAI", "True"
).lower() in ("true", "1")
MODEL = "gemini-2.5-pro"

client = None
if GOOGLE_CLOUD_PROJECT:
    try:
        client = genai.Client(
            vertexai=GOOGLE_GENAI_USE_VERTEXAI,
            project=GOOGLE_CLOUD_PROJECT,
            location=GOOGLE_CLOUD_LOCATION,
        )
        logger.info(
            f"GenAI Client initialized. VertexAI: {GOOGLE_GENAI_USE_VERTEXAI}, Project: {GOOGLE_CLOUD_PROJECT}, Location: {GOOGLE_CLOUD_LOCATION}, Model: {MODEL}"
        )
    except Exception as e:
        logger.error(f"Failed to initialize GenAI Client: {e}")
else:
    logger.error("Cannot initialize GenAI Client: GOOGLE_CLOUD_PROJECT is not set.")


def _execute_query(conn: Any, query: str) -> list[dict[str, Any]]:
    """Executes a SQL query and returns results as a list of dicts."""
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query)
        return cursor.fetchall()
    finally:
        cursor.close()


def _construct_llm_prompt(
    schema_name: str, db_type: str, schema_details: dict[str, Any]
) -> str:
    """Constructs a prompt for the LLM to analyze relationships and anomalies with formatted JSON."""

    tables_context = {}
    for table_name, table_info in schema_details.get("tables", {}).items():
        tables_context[table_name] = {
            "columns": list(table_info.get("columns", {}).keys()),
            "constraints": table_info.get("constraints", []),
        }

    context = {
        "db_type": db_type,
        "schema_name": schema_name,
        "tables": tables_context,
        "existing_foreign_keys": schema_details.get("foreign_keys", []),
    }

    # Format JSON for readability
    context_json = json.dumps(context, indent=4)

    prompt = f"""
    You are a database expert analyzing the schema of a {db_type} database named '{schema_name}'.
    Your task is to identify potential inferred relationships and relationship anomalies based on the provided schema information.

    Here is the schema context:
    ```json
    {context_json}
    ```

    **Tasks:**

    1.  **Inferred Relationship Suggestion:**
        Analyze the table and column names. Suggest potential foreign key relationships that are NOT already defined in `existing_foreign_keys`.
        Common patterns include columns like `user_id`, `product_code`, `order_uuid`, etc., potentially linking to `id` or similar columns in other tables (e.g., `users.id`).
        For each suggestion, provide the `from_table`, `from_column`, `to_table`, `to_column`, an `explanation` (why you think it's related), and a `suggestion` (e.g., "Consider adding a foreign key").

    2.  **Relationship Anomaly Detection:**
        Examine the `existing_foreign_keys`. For each foreign key, check if the `to_table` and `to_column` exist in the `tables` context. Also, verify if the `to_column` in the `to_table` is part of a PRIMARY KEY or UNIQUE constraint in that table's constraints list.
        Flag any anomalies where:
            a. The `to_table` is not in the `tables` context.
            b. The `to_column` is not in the `columns` list of the `to_table`.
            c. The `to_column` in the `to_table` is NOT listed as a 'PRIMARY KEY' or 'UNIQUE' in its constraints.
        For each anomaly, provide the `constraint_name`, `from_table`, `from_column`, `to_table`, `to_column`, an `explanation` of the issue, and a `suggestion` (e.g., "Verify target column exists" or "Target column should be PK/UK").

    **Output Format:**
    Return your findings as a single JSON object with two keys: "inferred_relationships" and "anomalies". The JSON must be well-formed.

    ```json
    {{
      "inferred_relationships": [
        {{
          "from_table": "string",
          "from_column": "string",
          "to_table": "string",
          "to_column": "string",
          "explanation": "string",
          "suggestion": "string"
        }}
      ],
      "anomalies": [
        {{
          "constraint_name": "string",
          "from_table": "string",
          "from_column": "string",
          "to_table": "string",
          "to_column": "string",
          "explanation": "string",
          "suggestion": "string"
        }}
      ]
    }}
    ```
    If no inferred relationships or anomalies are found, return empty lists for the respective keys.
    """
    return prompt


def _extract_json_content(text: str) -> str:
    """
    Extracts JSON content from Markdown-style code fences (```json ... ```).
    If no fences are present, returns the text as-is.
    """
    if not text:
        return ""

    match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        extracted = match.group(1).strip()
    else:
        extracted = text.strip()

    try:
        parsed = json.loads(extracted)
        return json.dumps(parsed, indent=4)
    except json.JSONDecodeError:
        return extracted


def _analyze_with_llm(
    schema_name: str, db_type: str, schema_details: dict[str, Any]
) -> dict[str, list[dict[str, Any]]]:
    """Calls an LLM to get inferred relationships and anomalies."""
    if not client:
        logger.error("GenAI Client not initialized. Skipping LLM analysis.")
        return {
            "inferred_relationships": [],
            "anomalies": [{"error": "LLM client not available."}],
        }

    prompt = _construct_llm_prompt(schema_name, db_type, schema_details)
    logger.info(f"Sending prompt to LLM for {db_type} relationship analysis.")
    generated_text = ""
    try:
        logger.debug(f"****** Custom_LLM_Request: {prompt}")
        response = client.models.generate_content(
            model=MODEL,
            contents=[types.Part.from_text(text=prompt)],  # type: ignore[arg-type]
        )
        generated_text = response.candidates[0].content.parts[0].text  # type: ignore[index, union-attr, assignment]
        logger.debug(f"****** Raw LLM Response: {generated_text}")

        # handles ```json blocks
        cleaned_json = _extract_json_content(generated_text)
        logger.debug(
            f"****** Cleaned JSON Extracted from LLM Response:\n{cleaned_json}"
        )

        # Parse the cleaned JSON
        llm_output = json.loads(cleaned_json)
        inferred = llm_output.get("inferred_relationships", [])
        anomalies = llm_output.get("anomalies", [])

        if not isinstance(inferred, list) or not isinstance(anomalies, list):
            raise ValueError(
                "LLM response is not in the expected list format for keys."
            )

        return {"inferred_relationships": inferred, "anomalies": anomalies}

    except json.JSONDecodeError as e:
        logger.error(
            f"Error decoding LLM JSON response: {e}. Cleaned Response: {cleaned_json}"
        )
        return {
            "inferred_relationships": [],
            "anomalies": [{"error": f"LLM response was not valid JSON: {e}"}],
        }
    except (exceptions.GoogleAPICallError, IndexError, AttributeError, ValueError) as e:
        logger.error(f"Error calling LLM or processing response: {e}")
        return {
            "inferred_relationships": [],
            "anomalies": [{"error": f"LLM analysis failed: {e}"}],
        }
    except Exception as e:
        logger.error(f"Unexpected error during LLM analysis: {e}")
        return {
            "inferred_relationships": [],
            "anomalies": [{"error": f"Unexpected LLM analysis error: {e}"}],
        }


def get_mysql_schema_details(conn: Any, schema_name: str) -> dict[str, Any]:
    # For MySQL, schema_name is the database name.
    logger.info(f"Fetching MySQL schema details for: {schema_name}")
    try:
        conn.database = schema_name
    except mysql.connector.Error as err:
        logger.error(f"MySQL change database failed: {err}")
        raise

    details: dict[str, Any] = {
        "tables": {},
        "views": {},
        "foreign_keys": [],
        "inferred_relationships": [],
        "anomalies": [],
    }

    # 1. Fetch Basic Schema Info
    tables_query = "SHOW FULL TABLES WHERE Table_type = 'BASE TABLE';"
    tables = _execute_query(conn, tables_query)
    table_names = [next(iter(t.values())) for t in tables]

    for t_name in table_names:
        details["tables"][t_name] = {"columns": {}, "constraints": [], "indexes": []}
        cols_query = f"DESCRIBE `{t_name}`;"
        columns = _execute_query(conn, cols_query)
        for col in columns:
            details["tables"][t_name]["columns"][col["Field"]] = {
                "type": col["Type"],
                "nullable": col["Null"] == "YES",
                "default": col["Default"],
                "key": col["Key"],
                "extra": col["Extra"],
            }

        constraints_query = f"""
            SELECT KCU.CONSTRAINT_NAME, TC.CONSTRAINT_TYPE, KCU.COLUMN_NAME
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS AS TC
            LEFT JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE AS KCU
                ON TC.CONSTRAINT_NAME = KCU.CONSTRAINT_NAME AND TC.TABLE_SCHEMA = KCU.TABLE_SCHEMA AND TC.TABLE_NAME = KCU.TABLE_NAME
            WHERE TC.TABLE_SCHEMA = '{schema_name}' AND TC.TABLE_NAME = '{t_name}'
            AND TC.CONSTRAINT_TYPE IN ('PRIMARY KEY', 'UNIQUE', 'FOREIGN KEY', 'CHECK');
        """
        details["tables"][t_name]["constraints"] = _execute_query(
            conn, constraints_query
        )

        indexes_query = f"SHOW INDEX FROM `{t_name}`;"
        indexes = _execute_query(conn, indexes_query)
        grouped_indexes = {}
        for index in indexes:
            idx_name = index["Key_name"]
            if idx_name not in grouped_indexes:
                grouped_indexes[idx_name] = {
                    "name": idx_name,
                    "columns": [],
                    "unique": index["Non_unique"] == 0,
                }
            grouped_indexes[idx_name]["columns"].append(index["Column_name"])
        details["tables"][t_name]["indexes"] = list(grouped_indexes.values())

    fks_query = f"""
        SELECT KCU.TABLE_NAME AS from_table, KCU.COLUMN_NAME AS from_column,
               KCU.REFERENCED_TABLE_NAME AS to_table, KCU.REFERENCED_COLUMN_NAME AS to_column, KCU.CONSTRAINT_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE AS KCU
        WHERE KCU.TABLE_SCHEMA = '{schema_name}' AND KCU.REFERENCED_TABLE_NAME IS NOT NULL;
    """
    details["foreign_keys"] = _execute_query(conn, fks_query)

    views_query = "SHOW FULL TABLES WHERE Table_type = 'VIEW';"
    views = _execute_query(conn, views_query)
    for v_name in [next(iter(v.values())) for v in views]:
        try:
            definition_query = f"SHOW CREATE VIEW `{v_name}`;"
            definition = _execute_query(conn, definition_query)
            details["views"][v_name] = {"definition": definition[0]["Create View"]}
        except Exception as e:
            logger.warning(f"Could not fetch view definition for {v_name}: {e}")
            details["views"][v_name] = {"definition": "N/A"}

    # 2. LLM-based Analysis for Inferred Relationships and Anomalies
    llm_analysis = _analyze_with_llm(schema_name, "MySQL", details)
    details["inferred_relationships"] = llm_analysis.get("inferred_relationships", [])
    details["anomalies"] = llm_analysis.get("anomalies", [])

    logger.info(
        f"Found {len(details['inferred_relationships'])} potential inferred relationships."
    )
    logger.info(f"Found {len(details['anomalies'])} potential relationship anomalies.")

    logger.debug("************************")
    logger.info(details)
    logger.debug("************************")

    return details
