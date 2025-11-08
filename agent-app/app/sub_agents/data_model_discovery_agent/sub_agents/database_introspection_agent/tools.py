import logging
import json
import psycopg2
from typing import Dict, Any
from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def execute_sql_query(sql_query: str, tool_context: ToolContext) -> Dict[str, Any]:
    """Executes a read-only SQL SELECT query using stored PostgreSQL connection metadata.

    Args:
        sql_query: The SQL SELECT statement to execute.
        tool_context: Provides session state containing saved database metadata.

    Returns:
        A dictionary with:
            - result: JSON string containing query results or an error message.
    """
    logger.info(f"Running SQL query: {sql_query}")

    # Ensure the query is read-only
    if not sql_query.strip().lower().startswith("select"):
        logger.warning("Only SELECT queries are allowed.")
        return {"result": json.dumps({"error": "Only SELECT queries are allowed."})}

    # Retrieve stored connection metadata
    db_conn = tool_context.state.get("db_connection")
    if not db_conn or db_conn.get("status") != "connected":
        logger.error("No valid database connection found.")
        return {"result": json.dumps({"error": "Database not connected or inactive."})}

    metadata = db_conn.get("metadata")
    if not metadata:
        logger.error("Database metadata missing in session state.")
        return {"result": json.dumps({"error": "Missing database metadata."})}

    try:
        # Create a temporary connection for query execution
        conn = psycopg2.connect(
            host=metadata["host"],
            port=metadata["port"],
            dbname=metadata["dbname"],
            user=metadata["user"],
            password="postgres",
        )

        # log the connection object
        logger.info(f"******* Connection object: {conn}")

        # Execute the query
        with conn.cursor() as cursor:
            cursor.execute(sql_query)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            result = [dict(zip(columns, row)) for row in rows]

        conn.close()
        logger.info(f"Query executed successfully — rows returned: {len(result)}")
        return {"result": json.dumps(result, default=str)}

    except Exception as e:
        logger.error(f"SQL execution failed: {e}")
        return {"result": json.dumps({"error": str(e)})}