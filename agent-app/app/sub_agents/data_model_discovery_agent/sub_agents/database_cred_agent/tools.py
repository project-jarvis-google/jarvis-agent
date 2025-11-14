from google.adk.tools import ToolContext
import logging
from typing import Dict, Any, List

# Import database connectors
import psycopg2
import mysql.connector
import pyodbc

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def _get_schemas(conn: Any, db_type: str) -> List[str]:
    """Fetches list of schemas/databases based on db type."""
    schemas = []
    cursor = conn.cursor()
    try:
        if db_type == "postgresql":
            cursor.execute(
                "SELECT schema_name FROM information_schema.schemata "
                "WHERE schema_name NOT LIKE 'pg_%' AND schema_name != 'information_schema';"
            )
            schemas = [row[0] for row in cursor.fetchall()]
        elif db_type == "mysql":
            cursor.execute("SHOW DATABASES;")
            # Filter out default mysql databases
            default_dbs = {'information_schema', 'mysql', 'performance_schema', 'sys'}
            schemas = [row[0] for row in cursor.fetchall() if row[0] not in default_dbs]
        elif db_type == "mssql":
            cursor.execute("SELECT name FROM sys.schemas;")
             # Filter out default mssql schemas
            default_schemas = {
                'db_accessadmin', 'db_backupoperator', 'db_datareader', 'db_datawriter',
                'db_ddladmin', 'db_denydatareader', 'db_denydatawriter', 'db_owner',
                'db_securityadmin', 'guest', 'INFORMATION_SCHEMA', 'sys'
            }
            schemas = [row[0] for row in cursor.fetchall() if row[0] not in default_schemas]
    finally:
        cursor.close()
    return schemas

async def validate_db_connection(connection_details: Dict[str, Any], tool_context: ToolContext) -> Dict[str, Any]:
    """Validates a database connection for PostgreSQL, MySQL, or MSSQL,
    fetches available schemas, and saves metadata to session memory.

    Args:
        connection_details: Database credentials including host, port, dbname, user, password,
            and db_type ("postgresql", "mysql", or "mssql").
        tool_context: The runtime context used to store session-level state.

    Returns:
        A dict with:
            - status: "success" if connection is valid, else "error".
            - message: Details about the validation result.
            - schemas: List of schemas (only on success).
    """
    safe_log = {k: v for k, v in connection_details.items() if k != "password"}
    logger.info(f"Attempting connection with details: {safe_log}")

    required_keys = ["host", "port", "dbname", "user", "password", "db_type"]
    missing_keys = [k for k in required_keys if k not in connection_details]
    if missing_keys:
        error_msg = f"Missing required parameters: {', '.join(missing_keys)}"
        logger.error(error_msg)
        return {"status": "error", "message": error_msg}

    db_type = connection_details["db_type"].lower()
    conn = None
    try:
        if db_type == "postgresql":
            conn = psycopg2.connect(
                host=connection_details["host"],
                port=connection_details["port"],
                dbname=connection_details["dbname"],
                user=connection_details["user"],
                password=connection_details["password"],
            )
        elif db_type == "mysql":
            conn = mysql.connector.connect(
                host=connection_details["host"],
                port=connection_details["port"],
                database=connection_details["dbname"],
                user=connection_details["user"],
                password=connection_details["password"],
            )
        elif db_type == "mssql":
            conn_str = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={connection_details['host']},{connection_details['port']};"
                f"DATABASE={connection_details['dbname']};"
                f"UID={connection_details['user']};"
                f"PWD={connection_details['password']}"
            )
            conn = pyodbc.connect(conn_str)
        else:
            error_msg = f"Unsupported database type: {db_type}. Supported types are: postgresql, mysql, mssql."
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}

        logger.info(f"{db_type.upper()} connection established successfully for validation.")

        # Fetch schemas
        schemas = _get_schemas(conn, db_type)
        logger.info(f"Successfully fetched schemas: {schemas}")

        # Clear any previous connection state
        if "db_connection" in tool_context.state:
            del tool_context.state["db_connection"]
        if "db_creds_temp" in tool_context.state:
             del tool_context.state["db_creds_temp"]
        if "selected_schema" in tool_context.state:
            del tool_context.state["selected_schema"]

        tool_context.state["db_connection"] = {
            "metadata": {
                "host": connection_details["host"],
                "port": connection_details["port"],
                "dbname": connection_details["dbname"],
                "user": connection_details["user"],
                "db_type": db_type,
            },
            "status": "connected",
        }
        tool_context.state["db_creds_temp"] = {"password": connection_details["password"]}

        logger.info("Connection metadata saved in session memory.")
        return {
            "status": "success",
            "message": f"{db_type.upper()} connection validated successfully.",
            "schemas": schemas
        }

    except Exception as e:
        logger.error(f"Database connection or schema fetch failed for {db_type}: {e}")
        if "db_connection" in tool_context.state:
            del tool_context.state["db_connection"]
        if "db_creds_temp" in tool_context.state:
            del tool_context.state["db_creds_temp"]
        return {"status": "error", "message": f"Connection/Schema fetch failed for {db_type}: {e}"}
