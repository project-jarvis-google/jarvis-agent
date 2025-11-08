import logging
from typing import Dict, Any, List
import pyodbc

logger = logging.getLogger(__name__)

def _execute_query(conn: Any, query: str) -> List[Dict[str, Any]]:
    """Executes a SQL query and returns results as a list of dicts."""
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        columns = [column[0] for column in cursor.description]
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        return results
    finally:
        cursor.close()

def get_mssql_schema_details(conn: Any, schema_name: str) -> Dict[str, Any]:
    logger.info(f"Fetching MSSQL schema details for: {schema_name}")
    details = {"tables": {}, "views": {}, "foreign_keys": []}

    # Tables
    tables_query = f"""
    SELECT TABLE_NAME
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_SCHEMA = '{schema_name}' AND TABLE_TYPE = 'BASE TABLE';
    """
    tables = _execute_query(conn, tables_query)

    for table in tables:
        t_name = table['TABLE_NAME']
        details["tables"][t_name] = {"columns": {}, "constraints": [], "indexes": []}

        # Columns
        cols_query = f"""
        SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, NUMERIC_PRECISION, NUMERIC_SCALE, IS_NULLABLE, COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = '{schema_name}' AND TABLE_NAME = '{t_name}';
        """
        columns = _execute_query(conn, cols_query)
        for col in columns:
             details["tables"][t_name]["columns"][col['COLUMN_NAME']] = {
                "type": col['DATA_TYPE'],
                "length": col['CHARACTER_MAXIMUM_LENGTH'],
                "precision": col['NUMERIC_PRECISION'],
                "scale": col['NUMERIC_SCALE'],
                "nullable": col['IS_NULLABLE'] == 'YES',
                "default": col['COLUMN_DEFAULT'],
            }

    # Constraints (PK, UNIQUE, CHECK)
    constraints_query = f"""
    SELECT
        KCU.TABLE_NAME,
        TC.CONSTRAINT_NAME,
        TC.CONSTRAINT_TYPE,
        KCU.COLUMN_NAME,
        CC.CHECK_CLAUSE
    FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS AS TC
    LEFT JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE AS KCU
        ON TC.CONSTRAINT_NAME = KCU.CONSTRAINT_NAME AND TC.TABLE_SCHEMA = KCU.TABLE_SCHEMA AND TC.TABLE_NAME = KCU.TABLE_NAME
    LEFT JOIN INFORMATION_SCHEMA.CHECK_CONSTRAINTS AS CC
        ON TC.CONSTRAINT_NAME = CC.CONSTRAINT_NAME AND TC.CONSTRAINT_SCHEMA = CC.CONSTRAINT_SCHEMA
    WHERE TC.TABLE_SCHEMA = '{schema_name}';
    """
    constraints = _execute_query(conn, constraints_query)
    for const in constraints:
        t_name = const['TABLE_NAME']
        if t_name in details["tables"]:
            details["tables"][t_name]["constraints"].append({
                "name": const['CONSTRAINT_NAME'],
                "type": const['CONSTRAINT_TYPE'],
                "columns": const['COLUMN_NAME'],
                "check_clause": const['CHECK_CLAUSE'],
            })

    # Indexes
    indexes_query = f"""
    SELECT
        t.name AS table_name,
        ind.name AS index_name,
        COL_NAME(ic.object_id, ic.column_id) AS column_name,
        ind.is_unique
    FROM sys.indexes ind
    INNER JOIN sys.index_columns ic ON  ind.object_id = ic.object_id AND ind.index_id = ic.index_id
    INNER JOIN sys.tables t ON ind.object_id = t.object_id
    INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
    WHERE s.name = '{schema_name}' AND ind.is_hypothetical = 0 AND ind.is_primary_key = 0 AND ind.type > 0
    ORDER BY t.name, ind.name, ic.key_ordinal;
    """
    try:
        indexes = _execute_query(conn, indexes_query)
        for index in indexes:
            t_name = index['table_name']
            if t_name in details["tables"]:
                idx_name = index['index_name']
                if not idx_name: continue
                found = False
                for existing_idx in details["tables"][t_name]["indexes"]:
                    if existing_idx["name"] == idx_name:
                        if index['column_name'] not in existing_idx["columns"]:
                             existing_idx["columns"].append(index['column_name'])
                        found = True
                        break
                if not found:
                     details["tables"][t_name]["indexes"].append({
                        "name": idx_name,
                        "columns": [index['column_name']],
                        "unique": index['is_unique']
                    })
    except Exception as e:
        logger.error(f"Error fetching MSSQL indexes: {e}")

    # Foreign Keys
    fks_query = f"""
    SELECT
         KCU1.CONSTRAINT_NAME AS fk_constraint_name
        ,KCU1.TABLE_SCHEMA AS from_schema
        ,KCU1.TABLE_NAME AS from_table
        ,KCU1.COLUMN_NAME AS from_column
        ,KCU2.TABLE_SCHEMA AS to_schema
        ,KCU2.TABLE_NAME AS to_table
        ,KCU2.COLUMN_NAME AS to_column
    FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS RC
    JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE KCU1
        ON KCU1.CONSTRAINT_CATALOG = RC.CONSTRAINT_CATALOG
        AND KCU1.CONSTRAINT_SCHEMA = RC.CONSTRAINT_SCHEMA
        AND KCU1.CONSTRAINT_NAME = RC.CONSTRAINT_NAME
    JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE KCU2
        ON KCU2.CONSTRAINT_CATALOG = RC.UNIQUE_CONSTRAINT_CATALOG
        AND KCU2.CONSTRAINT_SCHEMA = RC.UNIQUE_CONSTRAINT_SCHEMA
        AND KCU2.CONSTRAINT_NAME = RC.UNIQUE_CONSTRAINT_NAME
        AND KCU2.ORDINAL_POSITION = KCU1.ORDINAL_POSITION
    WHERE KCU1.TABLE_SCHEMA = '{schema_name}';
    """
    try:
        details["foreign_keys"] = _execute_query(conn, fks_query)
    except Exception as e:
        logger.error(f"Error fetching MSSQL foreign keys: {e}")
        details["foreign_keys"] = [{"error": str(e)}]

    # Views
    views_query = f"""
    SELECT TABLE_NAME AS view_name, VIEW_DEFINITION
    FROM INFORMATION_SCHEMA.VIEWS
    WHERE TABLE_SCHEMA = '{schema_name}';
    """
    views = _execute_query(conn, views_query)
    for view in views:
        details["views"][view['view_name']] = {"definition": view['VIEW_DEFINITION']}

    return details
