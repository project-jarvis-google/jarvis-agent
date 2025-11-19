import logging
from typing import Dict, Any, List
import psycopg2
import json
import os
import re
from google import genai
from google.api_core import exceptions
from google.genai import types
import google.auth

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# --- LLM Client Setup ---
try:
    _, project_id = google.auth.default()
    GOOGLE_CLOUD_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", project_id)
except google.auth.exceptions.DefaultCredentialsError:
    GOOGLE_CLOUD_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT")

if not GOOGLE_CLOUD_PROJECT:
    logger.warning("GOOGLE_CLOUD_PROJECT not set in environment or Application Default Credentials.")

GOOGLE_CLOUD_LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
GOOGLE_GENAI_USE_VERTEXAI = os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "True").lower() in ("true", "1")
MODEL = os.environ.get("MODEL", "gemini-2.5-pro")

client = None
if GOOGLE_CLOUD_PROJECT:
    try:
        client = genai.Client(
            vertexai=GOOGLE_GENAI_USE_VERTEXAI,
            project=GOOGLE_CLOUD_PROJECT,
            location=GOOGLE_CLOUD_LOCATION,
        )
        logger.info(f"GenAI Client initialized in postgres_utils. VertexAI: {GOOGLE_GENAI_USE_VERTEXAI}, Project: {GOOGLE_CLOUD_PROJECT}, Location: {GOOGLE_CLOUD_LOCATION}, Model: {MODEL}")
    except Exception as e:
        logger.error(f"Failed to initialize GenAI Client in postgres_utils: {e}")
else:
    logger.error("Cannot initialize GenAI Client in postgres_utils: GOOGLE_CLOUD_PROJECT is not set.")

def _execute_query(conn: Any, query: str) -> List[Dict[str, Any]]:
    """Executes a SQL query and returns results as a list of dicts for PostgreSQL."""
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        if cursor.description:
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        return []
    finally:
        cursor.close()

def _construct_llm_prompt(schema_name: str, db_type: str, schema_details: Dict[str, Any]) -> str:
    """Constructs a prompt for the LLM to analyze relationships and anomalies with formatted JSON."""
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
        logger.debug(f"****** Custom_LLM_Request: {prompt}")
        response = client.models.generate_content(
            model=MODEL,
            contents=[types.Part.from_text(text=prompt)],
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        generated_text = response.candidates[0].content.parts[0].text
        logger.debug(f"****** Raw LLM Response: {generated_text}")
        cleaned_json = _extract_json_content(generated_text)
        logger.debug(f"****** Cleaned JSON Extracted from LLM Response:\n{cleaned_json}")
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

def get_postgres_schema_details(conn: Any, schema_name: str) -> Dict[str, Any]:
    details = {"tables": {}, "views": {}, "foreign_keys": [], "inferred_relationships": [], "anomalies": []}
    logger.info(f"Fetching PostgreSQL schema details for: {schema_name}")

    tables_query = f"SELECT table_name FROM information_schema.tables WHERE table_schema = '{schema_name}' AND table_type = 'BASE TABLE';"
    tables = _execute_query(conn, tables_query)
    for table in tables:
        t_name = table['table_name']
        details["tables"][t_name] = {"columns": {}, "constraints": [], "indexes": []}
        cols_query = f"""
        SELECT column_name, data_type, character_maximum_length, numeric_precision, numeric_scale, is_nullable, column_default
        FROM information_schema.columns WHERE table_schema = '{schema_name}' AND table_name = '{t_name}';
        """
        for col in _execute_query(conn, cols_query):
            details["tables"][t_name]["columns"][col['column_name']] = {
                "type": col['data_type'], "length": col['character_maximum_length'], "precision": col['numeric_precision'],
                "scale": col['numeric_scale'], "nullable": col['is_nullable'] == 'YES', "default": col['column_default'],
            }
        constraints_query = f"""
        SELECT tc.table_name, tc.constraint_name, tc.constraint_type, kcu.column_name, cc.check_clause
        FROM information_schema.table_constraints tc
        LEFT JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema AND tc.table_name = kcu.table_name
        LEFT JOIN information_schema.check_constraints cc ON tc.constraint_name = cc.constraint_name AND tc.table_schema = cc.constraint_schema
        WHERE tc.table_schema = '{schema_name}' AND tc.table_name = '{t_name}';
        """
        details["tables"][t_name]["constraints"] = _execute_query(conn, constraints_query)
        indexes_query = f"""
        SELECT t.relname AS table_name, i.relname AS index_name, a.attname AS column_name, ix.indisunique AS is_unique
        FROM pg_class t JOIN pg_index ix ON t.oid = ix.indrelid JOIN pg_class i ON i.oid = ix.indexrelid
        LEFT JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
        JOIN pg_namespace n ON t.relnamespace = n.oid WHERE n.nspname = '{schema_name}' AND t.relname = '{t_name}' AND t.relkind = 'r';
        """
        try:
            indexes = _execute_query(conn, indexes_query)
            grouped_indexes = {}
            for index in indexes:
                if index['column_name']:
                    idx_name = index['index_name']
                    if idx_name not in grouped_indexes: grouped_indexes[idx_name] = {"name": idx_name, "columns": [], "unique": index['is_unique']}
                    if index['column_name'] not in grouped_indexes[idx_name]["columns"]: grouped_indexes[idx_name]["columns"].append(index['column_name'])
            details["tables"][t_name]["indexes"] = list(grouped_indexes.values())
        except Exception as e: logger.error(f"Error fetching PostgreSQL indexes for {t_name}: {e}")

    fks_query = f"""
    SELECT tc.constraint_name, tc.table_name AS from_table, kcu.column_name AS from_column,
           ccu.table_schema AS to_schema, ccu.table_name AS to_table, ccu.column_name AS to_column
    FROM information_schema.table_constraints AS tc JOIN information_schema.key_column_usage AS kcu
        ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
    JOIN information_schema.constraint_column_usage AS ccu
        ON ccu.constraint_name = tc.constraint_name AND ccu.table_schema = tc.table_schema
    WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = '{schema_name}';
    """
    details["foreign_keys"] = _execute_query(conn, fks_query)
    views_query = f"SELECT table_name AS view_name, view_definition FROM information_schema.views WHERE table_schema = '{schema_name}';"
    for view in _execute_query(conn, views_query): details["views"][view['view_name']] = {"definition": view['view_definition']}

    llm_analysis = _analyze_with_llm(schema_name, "PostgreSQL", details)
    details["inferred_relationships"] = llm_analysis.get("inferred_relationships", [])
    details["anomalies"] = llm_analysis.get("anomalies", [])
    logger.info(f"Found {len(details['inferred_relationships'])} potential inferred relationships for PostgreSQL.")
    logger.info(f"Found {len(details['anomalies'])} potential relationship anomalies for PostgreSQL.")
    return details
