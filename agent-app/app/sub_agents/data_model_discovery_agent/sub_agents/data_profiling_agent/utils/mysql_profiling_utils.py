import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def _execute_query(conn: Any, query: str) -> List[Dict[str, Any]]:
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query)
        return cursor.fetchall()
    finally:
        cursor.close()


def profile_mysql_data(
    conn: Any,
    schema_name: str,
    schema_structure: Dict[str, Any],
    sample_size: int = 10000,
) -> Dict[str, Any]:
    try:
        conn.database = schema_name
    except Exception as e:
        logger.error(f"Failed to set database {schema_name}: {e}")
        raise

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
        # Nullability
        for col_name in table_info.get("columns", {}):
            null_q = f"""
            SELECT
                COUNT(*) as total_count,
                SUM(CASE WHEN `{col_name}` IS NULL THEN 1 ELSE 0 END) as null_count
            FROM (SELECT `{col_name}` FROM `{table_name}` LIMIT {sample_size}) as sampled;
            """
            try:
                res = _execute_query(conn, null_q)[0]
                null_pct = (
                    (res["null_count"] / res["total_count"]) * 100
                    if res["total_count"] > 0
                    else 0
                )
                profile_results["nullability"][table_name][col_name] = round(
                    null_pct, 2
                )
            except Exception as e:
                logger.error(f"Error profiling nulls for {table_name}.{col_name}: {e}")
                profile_results["nullability"][table_name][col_name] = "Error"

        # Cardinality - PKs, FKs
        key_columns = set()
        for const in table_info.get("constraints", []):
            if const.get("type") in ("PRIMARY KEY", "UNIQUE") and const.get("columns"):
                key_columns.add(const["columns"])
        for fk in schema_structure.get("foreign_keys", []):
            if fk.get("from_table") == table_name and fk.get("from_column"):
                key_columns.add(fk["from_column"])

        for col_name in key_columns:
            if col_name in table_info.get("columns", {}):
                card_q = f"SELECT COUNT(DISTINCT `{col_name}`) as unique_count FROM `{table_name}`;"
                try:
                    res = _execute_query(conn, card_q)[0]
                    profile_results["cardinality"][table_name][col_name] = res[
                        "unique_count"
                    ]
                except Exception as e:
                    logger.error(
                        f"Error profiling cardinality for {table_name}.{col_name}: {e}"
                    )
                    profile_results["cardinality"][table_name][col_name] = "Error"

    # Orphan Records
    for fk in schema_structure.get("foreign_keys", []):
        from_table, from_col = fk.get("from_table"), fk.get("from_column")
        to_table, to_col = fk.get("to_table"), fk.get("to_column")
        if from_table and from_col and to_table and to_col:
            fk_name = f"{from_table}.{from_col} -> {to_table}.{to_col}"
            logger.info(f"Checking orphans for {fk_name}")
            orphan_q = f"""
            SELECT
                COUNT(s.`{from_col}`) as total_fk_values,
                SUM(CASE WHEN t.`{to_col}` IS NULL THEN 1 ELSE 0 END) as orphan_count
            FROM (SELECT `{from_col}` FROM `{from_table}` WHERE `{from_col}` IS NOT NULL LIMIT {sample_size}) as s
            LEFT JOIN `{to_table}` t ON s.`{from_col}` = t.`{to_col}`;
            """
            try:
                res = _execute_query(conn, orphan_q)[0]
                orphan_pct = (
                    (res["orphan_count"] / res["total_fk_values"]) * 100
                    if res["total_fk_values"] > 0
                    else 0
                )
                profile_results["orphan_records"][fk_name] = round(orphan_pct, 2)
            except Exception as e:
                logger.error(f"Error checking orphans for {fk_name}: {e}")
                profile_results["orphan_records"][fk_name] = "Error"

    # Type Anomalies - Heuristic for phone/zip
    for table_name, table_info in tables.items():
        for col_name, col_info in table_info.get("columns", {}).items():
            col_type = col_info.get("type", "").lower()
            if "char" in col_type or "text" in col_type:
                if (
                    "phone" in col_name.lower()
                    or "zip" in col_name.lower()
                    or "postal" in col_name.lower()
                ):
                    anomaly_q = f"""
                    SELECT COUNT(*) as non_numeric_count
                    FROM (SELECT `{col_name}` FROM `{table_name}` WHERE `{col_name}` IS NOT NULL LIMIT {sample_size}) as s
                    WHERE `{col_name}` REGEXP '[^0-9.-]';
                    """
                    try:
                        res = _execute_query(conn, anomaly_q)[0]
                        if res["non_numeric_count"] > 0:
                            key = f"{table_name}.{col_name}"
                            if key not in profile_results["type_anomalies"]:
                                profile_results["type_anomalies"][key] = []
                            profile_results["type_anomalies"][key].append(
                                f"Found {res['non_numeric_count']} rows with non-numeric characters in sample."
                            )
                    except Exception as e:
                        logger.warning(
                            f"Error checking type anomaly for {table_name}.{col_name}: {e}"
                        )
    return profile_results
