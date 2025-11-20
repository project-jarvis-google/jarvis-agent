import logging
from typing import Any

import mysql.connector

# Import database connectors
import psycopg2
import pyodbc
from google.adk.tools import ToolContext

# Import utils
from .utils import mssql_utils, mysql_utils, postgresql_utils

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def _get_db_connection(metadata: dict[str, Any], password: str) -> Any:
    db_type = metadata.get("db_type")
    host = metadata.get("host")
    port = metadata.get("port")
    dbname = metadata.get("dbname")
    user = metadata.get("user")

    if not all([db_type, host, port, dbname, user, password is not None]):
        raise ValueError(
            "Missing one or more required connection parameters in metadata or password."
        )
    port = int(port)  # type: ignore[arg-type]
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


def _generate_summary(schema_details: dict[str, Any]) -> dict[str, int]:
    """Generates a summary of the introspected schema structure."""
    summary = {
        "tables": len(schema_details.get("tables", {})),
        "views": len(schema_details.get("views", {})),
        "explicit_fks": len(schema_details.get("foreign_keys", [])),
        "inferred_relationships": len(schema_details.get("inferred_relationships", [])),
        "anomalies": len(schema_details.get("anomalies", [])),
        "columns": 0,
        "constraints": 0,
        "indexes": 0,
    }
    for table_info in schema_details.get("tables", {}).values():
        summary["columns"] += len(table_info.get("columns", {}))
        summary["constraints"] += len(table_info.get("constraints", []))
        summary["indexes"] += len(table_info.get("indexes", []))
    return summary


async def get_schema_details(
    tool_context: ToolContext, args: dict[str, Any]
) -> dict[str, Any]:
    """
    Retrieves detailed schema information and a summary for the given schema_name.
    Updates the session state with the selected_schema and schema_structure.
    """
    schema_name = args.get("schema_name")
    if not schema_name or not str(schema_name).strip():
        return {"error": "schema_name not provided in args or is empty."}
    schema_name = str(schema_name).strip()

    db_conn_state = tool_context.state.get("db_connection")
    db_creds = tool_context.state.get("db_creds_temp")

    if not db_conn_state or db_conn_state.get("status") != "connected":
        return {"error": "Database not connected. Please connect first."}
    if not db_creds:
        return {"error": "Database credentials not found."}

    tool_context.state["selected_schema"] = schema_name
    if "available_schemas" in tool_context.state:
        tool_context.state["available_schemas"] = None

    metadata = db_conn_state["metadata"]
    password = db_creds["password"]
    db_type = metadata["db_type"]

    conn = None
    try:
        conn = _get_db_connection(metadata, password)
        logger.info(
            f"Successfully reconnected to {db_type} for introspection of schema '{schema_name}'."
        )

        if db_type == "postgresql":
            schema_details = postgresql_utils.get_postgres_schema_details(
                conn, schema_name
            )
        elif db_type == "mysql":
            schema_details = mysql_utils.get_mysql_schema_details(conn, schema_name)
        elif db_type == "mssql":
            schema_details = mssql_utils.get_mssql_schema_details(conn, schema_name)
        else:
            return {"error": f"Introspection for {db_type} is not implemented."}

        tool_context.state["schema_structure"] = schema_details
        logger.info(f"Schema structure for '{schema_name}' saved to session state.")

        summary = _generate_summary(schema_details)

        return {
            "status": "success",
            "message": f"Schema details for '{schema_name}' ({db_type}) retrieved and stored.",
            "schema_name": schema_name,
            "summary": summary,  # Include the summary
        }
    except Exception as e:
        logger.error(f"Error during schema introspection: {e}", exc_info=True)
        return {
            "error": f"Failed to get schema details for {db_type} ({schema_name}): {e!s}"
        }
    finally:
        if conn:
            try:
                conn.close()
            except Exception as e:
                logger.error(f"Error closing {db_type} connection: {e}")
