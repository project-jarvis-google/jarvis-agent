import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

def _execute_query(conn: Any, query: str) -> List[Dict[str, Any]]:
    """Executes a SQL query and returns results as a list of dicts."""
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

def get_postgres_schema_details(conn: Any, schema_name: str) -> Dict[str, Any]:
    details = {"tables": {}, "views": {}, "foreign_keys": []}
    logger.info(f"Fetching PostgreSQL schema details for: {schema_name}")

    # Tables and Columns
    tables_query = f"""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = '{schema_name}' AND table_type = 'BASE TABLE';
    """
    tables = _execute_query(conn, tables_query)

    for table in tables:
        t_name = table['table_name']
        details["tables"][t_name] = {"columns": {}, "constraints": [], "indexes": []}

        cols_query = f"""
        SELECT column_name, data_type, character_maximum_length, numeric_precision, numeric_scale, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_schema = '{schema_name}' AND table_name = '{t_name}';
        """
        columns = _execute_query(conn, cols_query)
        for col in columns:
            details["tables"][t_name]["columns"][col['column_name']] = {
                "type": col['data_type'],
                "length": col['character_maximum_length'],
                "precision": col['numeric_precision'],
                "scale": col['numeric_scale'],
                "nullable": col['is_nullable'] == 'YES',
                "default": col['column_default'],
            }

    # Constraints (PK, UNIQUE, CHECK)
    constraints_query = f"""
    SELECT
        tc.table_name,
        tc.constraint_name,
        tc.constraint_type,
        kcu.column_name,
        cc.check_clause
    FROM information_schema.table_constraints tc
    LEFT JOIN information_schema.key_column_usage kcu
        ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema AND tc.table_name = kcu.table_name
    LEFT JOIN information_schema.check_constraints cc
        ON tc.constraint_name = cc.constraint_name AND tc.table_schema = cc.constraint_schema
    WHERE tc.table_schema = '{schema_name}' AND tc.table_name IN (SELECT table_name FROM information_schema.tables WHERE table_schema = '{schema_name}' AND table_type = 'BASE TABLE');
    """
    constraints = _execute_query(conn, constraints_query)
    for const in constraints:
        t_name = const['table_name']
        if t_name in details["tables"]:
            details["tables"][t_name]["constraints"].append({
                "name": const['constraint_name'],
                "type": const['constraint_type'],
                "columns": const['column_name'],
                "check_clause": const['check_clause'],
            })

    # Indexes
    indexes_query = f"""
    SELECT
        t.relname AS table_name,
        i.relname AS index_name,
        a.attname AS column_name,
        ix.indisunique AS is_unique
    FROM pg_class t
    JOIN pg_index ix ON t.oid = ix.indrelid
    JOIN pg_class i ON i.oid = ix.indexrelid
    LEFT JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
    JOIN pg_namespace n ON t.relnamespace = n.oid
    WHERE n.nspname = '{schema_name}' AND t.relkind = 'r';
    """
    try:
        indexes = _execute_query(conn, indexes_query)
        for index in indexes:
            t_name = index['table_name']
            if t_name in details["tables"] and index['column_name']:
                idx_name = index['index_name']
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
        logger.error(f"Error fetching PostgreSQL indexes: {e}")

    # Foreign Keys
    fks_query = f"""
    SELECT
        tc.table_name AS from_table,
        kcu.column_name AS from_column,
        ccu.table_name AS to_table,
        ccu.column_name AS to_column,
        tc.constraint_name
    FROM information_schema.table_constraints AS tc
    JOIN information_schema.key_column_usage AS kcu
        ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
    JOIN information_schema.constraint_column_usage AS ccu
        ON ccu.constraint_name = tc.constraint_name AND ccu.table_schema = tc.table_schema
    WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = '{schema_name}';
    """
    details["foreign_keys"] = _execute_query(conn, fks_query)

    # Views
    views_query = f"""
    SELECT table_name AS view_name, view_definition
    FROM information_schema.views
    WHERE table_schema = '{schema_name}';
    """
    views = _execute_query(conn, views_query)
    for view in views:
        details["views"][view['view_name']] = {"definition": view['view_definition']}

    return details
