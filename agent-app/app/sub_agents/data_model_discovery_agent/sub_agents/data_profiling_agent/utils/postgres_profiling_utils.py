import logging
from typing import Any

logger = logging.getLogger(__name__)


def _execute_query(conn: Any, query: str) -> list[dict[str, Any]]:
    """Executes a SQL query and returns results as a list of dicts for PostgreSQL."""
    cursor = conn.cursor()
    try:
        conn.autocommit = True
        cursor.execute(query)
        if cursor.description:
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(columns, row, strict=False)) for row in rows]
        return []
    finally:
        cursor.close()


def profile_postgres_data(
    conn: Any,
    schema_name: str,
    schema_structure: dict[str, Any],
    sample_size: int = 10000,
) -> dict[str, Any]:
    profile_results = {
        "nullability": {},
        "cardinality": {},
        "orphan_records": {},
        "type_anomalies": {},
    }
    tables = schema_structure.get("tables", {})

    for table_name, table_info in tables.items():
        logger.info(f"Profiling table: {schema_name}.{table_name}")
        profile_results["nullability"][table_name] = {}
        profile_results["cardinality"][table_name] = {}
        full_table_name = f'"{schema_name}"."{table_name}"'

        for col_name in table_info.get("columns", {}):
            null_q = f"""
            SELECT
                COUNT(*) as total_count,
                COUNT(*) - COUNT("{col_name}") as null_count
            FROM (SELECT "{col_name}" FROM {full_table_name} LIMIT {sample_size}) as sampled;
            """
            try:
                res = _execute_query(conn, null_q)[0]
                total_count = int(res["total_count"])
                null_count = int(res["null_count"])
                null_pct = (null_count / total_count) * 100 if total_count > 0 else 0
                profile_results["nullability"][table_name][col_name] = round(
                    null_pct, 2
                )
            except Exception as e:
                logger.error(
                    f'Error profiling nulls for {full_table_name}."{col_name}": {e}'
                )
                profile_results["nullability"][table_name][col_name] = "Error"

        key_columns = set()
        for const in table_info.get("constraints", []):
            if const.get("type") in ("PRIMARY KEY", "UNIQUE") and const.get("columns"):
                key_columns.add(const["columns"])
        for fk in schema_structure.get("foreign_keys", []):
            if fk.get("from_table") == table_name and fk.get("from_column"):
                key_columns.add(fk["from_column"])

        for col_name in key_columns:
            if col_name in table_info.get("columns", {}):
                card_q = f'SELECT COUNT(DISTINCT "{col_name}") as unique_count FROM {full_table_name};'
                try:
                    res = _execute_query(conn, card_q)[0]
                    profile_results["cardinality"][table_name][col_name] = int(
                        res["unique_count"]
                    )
                except Exception as e:
                    logger.error(
                        f'Error profiling cardinality for {full_table_name}."{col_name}": {e}'
                    )
                    profile_results["cardinality"][table_name][col_name] = "Error"

    for fk in schema_structure.get("foreign_keys", []):
        from_table, from_col = fk.get("from_table"), fk.get("from_column")
        to_table, to_col = fk.get("to_table"), fk.get("to_column")
        to_schema = fk.get(
            "to_schema", schema_name
        )  # Assume same schema if not specified
        if from_table and from_col and to_table and to_col:
            fk_name = f"{from_table}.{from_col} -> {to_table}.{to_col}"
            logger.info(f"Checking orphans for {fk_name}")
            from_full = f'"{schema_name}"."{from_table}"'
            to_full = f'"{to_schema}"."{to_table}"'
            orphan_q = f"""
            SELECT
                COUNT(s."{from_col}") as total_fk_values,
                SUM(CASE WHEN t."{to_col}" IS NULL THEN 1 ELSE 0 END) as orphan_count
            FROM (SELECT "{from_col}" FROM {from_full} WHERE "{from_col}" IS NOT NULL LIMIT {sample_size}) as s
            LEFT JOIN {to_full} t ON s."{from_col}" = t."{to_col}";
            """
            try:
                res = _execute_query(conn, orphan_q)[0]
                total_fk_values = int(res["total_fk_values"])
                orphan_count = int(res["orphan_count"])
                orphan_pct = (
                    (orphan_count / total_fk_values) * 100 if total_fk_values > 0 else 0
                )
                profile_results["orphan_records"][fk_name] = round(orphan_pct, 2)
            except Exception as e:
                logger.error(f"Error checking orphans for {fk_name}: {e}")
                profile_results["orphan_records"][fk_name] = "Error"

    for table_name, table_info in tables.items():
        full_table_name = f'"{schema_name}"."{table_name}"'
        for col_name, col_info in table_info.get("columns", {}).items():
            col_type = col_info.get("type", "").lower()
            if "char" in col_type or "text" in col_type:
                if (
                    "phone" in col_name.lower()
                    or "zip" in col_name.lower()
                    or "postal" in col_name.lower()
                ):
                    # Regex for anything not a digit, hyphen, or period
                    anomaly_q = f"""
                    SELECT COUNT(*) as non_numeric_count
                    FROM (SELECT "{col_name}" FROM {full_table_name} WHERE "{col_name}" IS NOT NULL LIMIT {sample_size}) as s
                    WHERE "{col_name}" ~ '[^0-9.-]';
                    """
                    try:
                        res = _execute_query(conn, anomaly_q)[0]
                        non_numeric_count = int(res["non_numeric_count"])
                        if non_numeric_count > 0:
                            key = f"{table_name}.{col_name}"
                            if key not in profile_results["type_anomalies"]:
                                profile_results["type_anomalies"][key] = []
                            profile_results["type_anomalies"][key].append(
                                f"Found {non_numeric_count} rows with non-numeric characters in sample."
                            )
                    except Exception as e:
                        logger.warning(
                            f'Error checking type anomaly for {full_table_name}."{col_name}": {e}'
                        )

    return profile_results
