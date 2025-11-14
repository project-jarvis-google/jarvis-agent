import logging
from typing import Dict, Any, List
import pyodbc
import json
import os
import re
from google import genai
from google.api_core import exceptions
from google.genai import types
import google.auth

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# --- Copied LLM Client Setup & Helper Functions ---
try:
    _, project_id = google.auth.default()
    GOOGLE_CLOUD_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", project_id)
except google.auth.exceptions.DefaultCredentialsError:
    GOOGLE_CLOUD_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT")

if not GOOGLE_CLOUD_PROJECT:
    logger.warning("GOOGLE_CLOUD_PROJECT not set.")

GOOGLE_CLOUD_LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
GOOGLE_GENAI_USE_VERTEXAI = os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "True").lower() in ("true", "1")
MODEL = os.environ.get("MODEL", "gemini-1.5-pro")

client = None
if GOOGLE_CLOUD_PROJECT:
    try:
        client = genai.Client(
            vertexai=GOOGLE_GENAI_USE_VERTEXAI,
            project=GOOGLE_CLOUD_PROJECT,
            location=GOOGLE_CLOUD_LOCATION,
        )
        logger.info(f"GenAI Client initialized in mssql_utils.")
    except Exception as e:
        logger.error(f"Failed to initialize GenAI Client in mssql_utils: {e}")
else:
     logger.error("Cannot initialize GenAI Client in mssql_utils: GOOGLE_CLOUD_PROJECT is not set.")

def _construct_llm_prompt(schema_name: str, db_type:str, schema_details: Dict[str, Any]) -> str:
    # ... This function is IDENTICAL to the one in mysql_utils.py ...
    tables_context = {}
    for table_name, table_info in schema_details.get("tables", {}).items():
        tables_context[table_name] = {
            "columns": list(table_info.get("columns", {}).keys()),
            "constraints": table_info.get("constraints", [])
        }
    context = {
        "db_type": db_type,
        "schema_name": schema_name,
        "tables": tables_context,
        "existing_foreign_keys": schema_details.get("foreign_keys", [])
    }
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
    """Extracts JSON content from Markdown-style code fences (```json ... ```)."""
    if not text: return ""
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    extracted = match.group(1).strip() if match else text.strip()
    try:
        parsed = json.loads(extracted)
        return json.dumps(parsed, indent=4)
    except json.JSONDecodeError:
        return extracted

def _analyze_with_llm(schema_name: str, db_type: str, schema_details: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """Calls an LLM to get inferred relationships and anomalies."""
    if not client:
        logger.error("GenAI Client not initialized. Skipping LLM analysis.")
        return {"inferred_relationships": [], "anomalies": [{"error": "LLM client not available."}]}

    prompt = _construct_llm_prompt(schema_name, db_type, schema_details)
    logger.info(f"Sending prompt to LLM for {db_type} relationship analysis.")
    generated_text = ""
    try:
        # logger.info(f"****** Custom_LLM_Request: {prompt}")
        response = client.models.generate_content(
            model=MODEL,
            contents=[types.Part.from_text(text=prompt)],
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        generated_text = response.candidates[0].content.parts[0].text
        # logger.info(f"****** Raw LLM Response: {generated_text}")
        cleaned_json = _extract_json_content(generated_text)
        # logger.info(f"****** Cleaned JSON Extracted from LLM Response:\n{cleaned_json}")
        llm_output = json.loads(cleaned_json)
        inferred = llm_output.get("inferred_relationships", [])
        anomalies = llm_output.get("anomalies", [])
        if not isinstance(inferred, list) or not isinstance(anomalies, list):
            raise ValueError("LLM response is not in the expected list format for keys.")
        return {"inferred_relationships": inferred, "anomalies": anomalies}
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding LLM JSON response: {e}. Cleaned Response: {cleaned_json}")
        return {"inferred_relationships": [], "anomalies": [{"error": f"LLM response was not valid JSON: {e}"}]}
    except (exceptions.GoogleAPICallError, IndexError, AttributeError, ValueError) as e:
        logger.error(f"Error calling LLM or processing response: {e}")
        return {"inferred_relationships": [], "anomalies": [{"error": f"LLM analysis failed: {e}"}]}
    except Exception as e:
        logger.error(f"Unexpected error during LLM analysis: {e}")
        return {"inferred_relationships": [], "anomalies": [{"error": f"Unexpected LLM analysis error: {e}"}]}
# --- End Copied LLM Functions ---

def _execute_query(conn: Any, query: str) -> List[Dict[str, Any]]:
    """Executes a SQL query and returns results as a list of dicts for SQL Server."""
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        if cursor.description:
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        return []
    finally:
        cursor.close()

def get_mssql_schema_details(conn: Any, schema_name: str) -> Dict[str, Any]:
    logger.info(f"Fetching MSSQL schema details for: {schema_name}")
    details = {"tables": {}, "views": {}, "foreign_keys": [], "inferred_relationships": [], "anomalies": []}

    tables_query = f"SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '{schema_name}' AND TABLE_TYPE = 'BASE TABLE';"
    tables = _execute_query(conn, tables_query)
    for table in tables:
        t_name = table['TABLE_NAME']
        details["tables"][t_name] = {"columns": {}, "constraints": [], "indexes": []}
        cols_query = f"SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, NUMERIC_PRECISION, NUMERIC_SCALE, IS_NULLABLE, COLUMN_DEFAULT FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = '{schema_name}' AND TABLE_NAME = '{t_name}';"
        for col in _execute_query(conn, cols_query):
             details["tables"][t_name]["columns"][col['COLUMN_NAME']] = {"type": col['DATA_TYPE'], "length": col['CHARACTER_MAXIMUM_LENGTH'], "precision": col['NUMERIC_PRECISION'], "scale": col['NUMERIC_SCALE'], "nullable": col['IS_NULLABLE'] == 'YES', "default": col['COLUMN_DEFAULT']}
        constraints_query = f"""
            SELECT KCU.TABLE_NAME, TC.CONSTRAINT_NAME, TC.CONSTRAINT_TYPE, KCU.COLUMN_NAME, CC.CHECK_CLAUSE
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS AS TC
            LEFT JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE AS KCU ON TC.CONSTRAINT_NAME = KCU.CONSTRAINT_NAME AND TC.TABLE_SCHEMA = KCU.TABLE_SCHEMA AND TC.TABLE_NAME = KCU.TABLE_NAME
            LEFT JOIN INFORMATION_SCHEMA.CHECK_CONSTRAINTS AS CC ON TC.CONSTRAINT_NAME = CC.CONSTRAINT_NAME AND TC.CONSTRAINT_SCHEMA = CC.CONSTRAINT_SCHEMA
            WHERE TC.TABLE_SCHEMA = '{schema_name}' AND KCU.TABLE_NAME = '{t_name}';
        """
        details["tables"][t_name]["constraints"] = _execute_query(conn, constraints_query)
        indexes_query = f"""
        SELECT t.name AS table_name, ind.name AS index_name, COL_NAME(ic.object_id, ic.column_id) AS column_name, ind.is_unique
        FROM sys.indexes ind INNER JOIN sys.index_columns ic ON  ind.object_id = ic.object_id AND ind.index_id = ic.index_id
        INNER JOIN sys.tables t ON ind.object_id = t.object_id INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
        WHERE s.name = '{schema_name}' AND t.name = '{t_name}' AND ind.is_hypothetical = 0 AND ind.is_primary_key = 0 AND ind.type > 0;
        """
        try:
            indexes = _execute_query(conn, indexes_query)
            grouped_indexes = {}
            for index in indexes:
                 idx_name = index['index_name']
                 if not idx_name: continue
                 if idx_name not in grouped_indexes: grouped_indexes[idx_name] = {"name": idx_name, "columns": [], "unique": index['is_unique']}
                 if index['column_name'] not in grouped_indexes[idx_name]["columns"]: grouped_indexes[idx_name]["columns"].append(index['column_name'])
            details["tables"][t_name]["indexes"] = list(grouped_indexes.values())
        except Exception as e: logger.error(f"Error fetching MSSQL indexes for {t_name}: {e}")

    fks_query = f"""
    SELECT KCU1.CONSTRAINT_NAME AS fk_constraint_name, KCU1.TABLE_SCHEMA AS from_schema, KCU1.TABLE_NAME AS from_table, KCU1.COLUMN_NAME AS from_column,
           KCU2.TABLE_SCHEMA AS to_schema, KCU2.TABLE_NAME AS to_table, KCU2.COLUMN_NAME AS to_column
    FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS RC
    JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE KCU1 ON KCU1.CONSTRAINT_SCHEMA = RC.CONSTRAINT_SCHEMA AND KCU1.CONSTRAINT_NAME = RC.CONSTRAINT_NAME
    JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE KCU2 ON KCU2.CONSTRAINT_SCHEMA = RC.UNIQUE_CONSTRAINT_SCHEMA AND KCU2.CONSTRAINT_NAME = RC.UNIQUE_CONSTRAINT_NAME AND KCU2.ORDINAL_POSITION = KCU1.ORDINAL_POSITION
    WHERE KCU1.TABLE_SCHEMA = '{schema_name}';
    """
    details["foreign_keys"] = _execute_query(conn, fks_query)
    views_query = f"SELECT TABLE_NAME AS view_name, VIEW_DEFINITION FROM INFORMATION_SCHEMA.VIEWS WHERE TABLE_SCHEMA = '{schema_name}';"
    for view in _execute_query(conn, views_query): details["views"][view['view_name']] = {"definition": view['VIEW_DEFINITION']}

    llm_analysis = _analyze_with_llm(schema_name, "Microsoft SQL Server", details)
    details["inferred_relationships"] = llm_analysis.get("inferred_relationships", [])
    details["anomalies"] = llm_analysis.get("anomalies", [])
    logger.info(f"Found {len(details['inferred_relationships'])} potential inferred relationships for MSSQL.")
    logger.info(f"Found {len(details['anomalies'])} potential relationship anomalies for MSSQL.")
    return details
