import logging
from typing import Any

import mysql.connector
import psycopg2
import pyodbc
from google.adk.tools import ToolContext

from .utils import (
    mssql_profiling_utils,
    mysql_profiling_utils,
    postgres_profiling_utils,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def _get_db_connection(metadata: dict[str, Any], password: str) -> Any:
    db_type = metadata.get("db_type")
    host = metadata.get("host")
    port = int(metadata.get("port"))
    dbname = metadata.get("dbname")
    user = metadata.get("user")
    logger.info(
        f"Attempting to connect to {db_type} at {host}:{port} as {user} to database {dbname}"
    )
    if db_type == "postgresql":
        return psycopg2.connect(
            host=host, port=port, dbname=dbname, user=user, password=password
        )
    elif db_type == "mysql":
        return mysql.connector.connect(
            host=host, port=port, database=dbname, user=user, password=password
        )
    elif db_type == "mssql":
        conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={host},{port};DATABASE={dbname};UID={user};PWD={password}"
        return pyodbc.connect(conn_str)
    else:
        raise ValueError(f"Unsupported database type: {db_type}")


async def profile_schema_data(
    tool_context: ToolContext, args: dict[str, Any]
) -> dict[str, Any]:
    """
    Profiles the data in the selected schema based on the schema structure.
    Calculates nullability, cardinality, orphan records, and type anomalies.
    Sets a flag on successful completion.
    """
    if not isinstance(args, dict):
        return {"error": "Invalid arguments. Expected a dictionary for args."}

    db_conn_state = tool_context.state.get("db_connection")
    db_creds = tool_context.state.get("db_creds_temp")
    schema_name = tool_context.state.get("selected_schema")
    schema_structure = tool_context.state.get("schema_structure")
    sample_size = args.get("sample_size", 10000)

    if not db_conn_state or db_conn_state.get("status") != "connected":
        return {"error": "DB not connected."}
    if not db_creds:
        return {"error": "DB credentials not found."}
    if not schema_name:
        return {"error": "Selected schema not found."}
    if not schema_structure:
        return {"error": "Schema structure not found. Please run introspection first."}

    metadata = db_conn_state["metadata"]
    password = db_creds["password"]
    db_type = metadata["db_type"]

    conn = None
    try:
        conn = _get_db_connection(metadata, password)
        logger.info(
            f"Reconnected to {db_type} for data profiling of schema '{schema_name}'."
        )

        if db_type == "postgresql":
            profile_results = postgres_profiling_utils.profile_postgres_data(
                conn, schema_name, schema_structure, sample_size
            )
        elif db_type == "mysql":
            profile_results = mysql_profiling_utils.profile_mysql_data(
                conn, schema_name, schema_structure, sample_size
            )
        elif db_type == "mssql":
            profile_results = mssql_profiling_utils.profile_mssql_data(
                conn, schema_name, schema_structure, sample_size
            )
        else:
            return {"error": f"Profiling for {db_type} not implemented."}

        tool_context.state["data_profile"] = profile_results
        tool_context.state["profiling_just_completed"] = True  # Set the flag
        logger.info(
            f"Data profiling results for '{schema_name}' saved to session state."
        )

        return {
            "status": "success",
            "message": f"Data profiling completed for schema '{schema_name}'. Results are stored.",
            "schema_name": schema_name,
        }
    except Exception as e:
        logger.error(f"Error during data profiling: {e}", exc_info=True)
        return {"error": f"Failed to profile data for {db_type} ({schema_name}): {e!s}"}
    finally:
        if conn:
            try:
                conn.close()
            except Exception as e:
                logger.error(f"Error closing {db_type} connection: {e}")
