import logging
from typing import Dict, Any, List
import mysql.connector

logger = logging.getLogger(__name__)

def _execute_query(conn: Any, query: str) -> List[Dict[str, Any]]:
    """Executes a SQL query and returns results as a list of dicts."""
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query)
        return cursor.fetchall()
    finally:
        cursor.close()

def get_mysql_schema_details(conn: Any, schema_name: str) -> Dict[str, Any]:
    # For MySQL, schema_name is the database name.
    logger.info(f"Fetching MySQL schema details for: {schema_name}")
    try:
        conn.database = schema_name
    except mysql.connector.Error as err:
        logger.error(f"MySQL change database failed: {err}")
        raise

    details = {"tables": {}, "views": {}, "foreign_keys": []}

    # Tables
    tables_query = "SHOW FULL TABLES WHERE Table_type = 'BASE TABLE';"
    tables = _execute_query(conn, tables_query)
    table_names = [list(t.values())[0] for t in tables]

    for t_name in table_names:
        details["tables"][t_name] = {"columns": {}, "constraints": [], "indexes": []}

        # Columns
        cols_query = f"DESCRIBE `{t_name}`;"
        columns = _execute_query(conn, cols_query)
        for col in columns:
            details["tables"][t_name]["columns"][col['Field']] = {
                "type": col['Type'],
                "nullable": col['Null'] == 'YES',
                "default": col['Default'],
                "key": col['Key'], # PRI, UNI, MUL
                "extra": col['Extra'],
            }

        # Constraints (PK, UNIQUE)
        constraints_query = f"""
        SELECT
            KCU.CONSTRAINT_NAME,
            TC.CONSTRAINT_TYPE,
            KCU.COLUMN_NAME
        FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS AS TC
        JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE AS KCU
            ON TC.CONSTRAINT_NAME = KCU.CONSTRAINT_NAME
            AND TC.TABLE_SCHEMA = KCU.TABLE_SCHEMA
            AND TC.TABLE_NAME = KCU.TABLE_NAME
        WHERE TC.TABLE_SCHEMA = '{schema_name}' AND TC.TABLE_NAME = '{t_name}'
        AND TC.CONSTRAINT_TYPE IN ('PRIMARY KEY', 'UNIQUE');
        """
        constraints = _execute_query(conn, constraints_query)
        for const in constraints:
            details["tables"][t_name]["constraints"].append({
                "name": const['CONSTRAINT_NAME'],
                "type": const['CONSTRAINT_TYPE'],
                "columns": const['COLUMN_NAME'],
            })
        # Note: MySQL CHECK constraints are in information_schema.CHECK_CONSTRAINTS

        # Indexes
        indexes_query = f"SHOW INDEX FROM `{t_name}`;"
        indexes = _execute_query(conn, indexes_query)
        grouped_indexes = {}
        for index in indexes:
            idx_name = index['Key_name']
            if idx_name not in grouped_indexes:
                grouped_indexes[idx_name] = {
                    "name": idx_name,
                    "columns": [],
                    "unique": index['Non_unique'] == 0
                }
            grouped_indexes[idx_name]["columns"].append(index['Column_name'])
        details["tables"][t_name]["indexes"] = list(grouped_indexes.values())

    # Foreign Keys
    fks_query = f"""
    SELECT
        KCU.TABLE_NAME AS from_table,
        KCU.COLUMN_NAME AS from_column,
        KCU.REFERENCED_TABLE_NAME AS to_table,
        KCU.REFERENCED_COLUMN_NAME AS to_column,
        KCU.CONSTRAINT_NAME
    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE AS KCU
    WHERE KCU.TABLE_SCHEMA = '{schema_name}'
    AND KCU.REFERENCED_TABLE_NAME IS NOT NULL;
    """
    details["foreign_keys"] = _execute_query(conn, fks_query)

    # Views
    views_query = "SHOW FULL TABLES WHERE Table_type = 'VIEW';"
    views = _execute_query(conn, views_query)
    view_names = [list(v.values())[0] for v in views]
    for v_name in view_names:
        try:
            definition_query = f"SHOW CREATE VIEW `{v_name}`;"
            definition = _execute_query(conn, definition_query)
            details["views"][v_name] = {"definition": definition[0]['Create View']}
        except Exception as e:
            logger.warning(f"Could not fetch view definition for {v_name}: {e}")
            details["views"][v_name] = {"definition": "N/A"}

    return details
