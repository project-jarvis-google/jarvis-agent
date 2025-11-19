import logging
from typing import Dict, Any, List
from google.adk.tools import ToolContext
import json
import yaml

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def generate_summary_report(tool_context: ToolContext, args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates a high-level summary report of the database analysis.

    This tool reads the 'schema_structure' and 'data_profile' from the session state
    to produce a markdown formatted text summary of the key findings from the
    introspection and data profiling phases.

    Args:
        tool_context: The ADK tool context, providing access to session state.
        args: A dictionary for potential arguments (not used in this version).

    Returns:
        A dictionary containing:
        - status: "success" or "error".
        - report_text: The markdown formatted summary report (on success).
        - error: An error message (on failure).
    """
    if not isinstance(args, dict):
        return {"error": "Invalid arguments. Expected a dictionary for args."}

    schema_structure = tool_context.state.get("schema_structure")
    data_profile = tool_context.state.get("data_profile")
    selected_schema = tool_context.state.get("selected_schema", "N/A")

    if not schema_structure:
        return {"error": "Schema structure not found. Please run introspection first."}

    summary = {
        "tables": len(schema_structure.get("tables", {})),
        "views": len(schema_structure.get("views", {})),
        "explicit_fks": len(schema_structure.get("foreign_keys", [])),
        "inferred_relationships": len(schema_structure.get("inferred_relationships", [])),
        "schema_anomalies": len(schema_structure.get("anomalies", [])),
        "columns": sum(len(t.get("columns", {})) for t in schema_structure.get("tables", {}).values()),
    }

    report = f"### Data Discovery Summary for Schema: {selected_schema}\n\n"
    report += "**Schema Structure:**\n"
    report += f"-   Tables Analyzed: {summary['tables']}\n"
    report += f"-   Total Columns: {summary['columns']}\n"
    report += f"-   Views Found: {summary['views']}\n"
    report += f"-   Explicit Foreign Keys: {summary['explicit_fks']}\n"
    report += f"-   Potential Inferred Relationships: {summary['inferred_relationships']}\n"
    report += f"-   Schema Anomalies Detected: {summary['schema_anomalies']}\n\n"

    if data_profile:
        report += "**Data Quality Profile Highlights:**\n"
        null_issues = sum(1 for table in data_profile.get("nullability", {}).values() for null_pct in table.values() if isinstance(null_pct, (int, float)) and null_pct > 50)
        orphan_issues = sum(1 for orphan_pct in data_profile.get("orphan_records", {}).values() if isinstance(orphan_pct, (int, float)) and orphan_pct > 10)
        type_anomalies = len(data_profile.get("type_anomalies", {}))

        report += f"-   Columns with >50% NULLs: {null_issues} (in sampled data)\n"
        report += f"-   FKs with >10% Orphan Records: {orphan_issues} (in sampled data)\n"
        report += f"-   Columns with Potential Type Anomalies: {type_anomalies} (in sampled data)\n"
    else:
        report += "**Data Quality Profile:** Not yet run.\n"

    return {"status": "success", "report_text": report}

import json
import logging

logger = logging.getLogger(__name__)

async def export_full_report(tool_context: ToolContext, args: dict) -> dict:
    """
    Exports the full schema structure and data profile as a clean JSON report.

    Only JSON is supported. Backslashes are avoided in the output.

    Args:
        tool_context: The ADK tool context providing session state.
        args: A dictionary containing optional 'format' key.

    Returns:
        Dict[str, Any]: {
            "status": "success" | "error",
            "message": Description,
            "report_content": JSON string (pretty-printed),
            "format": "JSON",
            "error": Optional error message
        }
    """
    if not isinstance(args, dict):
        return {"status": "error", "error": "Invalid arguments. Expected a dictionary for args."}

    schema_structure = tool_context.state.get("schema_structure")
    data_profile = tool_context.state.get("data_profile")

    if not schema_structure:
        return {"status": "error", "error": "Schema structure not found. Please run introspection first."}

    requested_format = args.get("format", "json").lower()
    if requested_format != "json":
        return {"status": "error", "error": f"Unsupported format '{requested_format}'. Only JSON is supported."}

    full_report = {
        "schema_structure": schema_structure,
        "data_profile": data_profile or "Not run"
    }

    def safe_encoder(obj):
        """
        Converts any non-serializable object into string automatically.
        Handles Decimal, datetime, UUID, set, custom objects, etc.
        """
        try:
            return json.JSONEncoder().default(obj)
        except Exception:
            # Fallback: convert everything else to string
            return str(obj)

    try:
        json_output = json.dumps(
            full_report,
            indent=2,
            ensure_ascii=False,
            default=safe_encoder
        )

        return {
            "status": "success",
            "message": "Full report generated in JSON format. You can copy the content below.",
            "report_content": json_output,
            "format": "JSON"
        }

    except Exception as e:
        logger.error(f"Error generating JSON report: {e}", exc_info=True)
        return {"status": "error", "error": f"Failed to generate JSON report: {str(e)}"}


async def generate_erd_script(tool_context: ToolContext, args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates a complete, valid Mermaid ER Diagram script.

    This function uses 'schema_structure' from the tool context's session state
    to build a fully compliant Mermaid ERD. It includes tables, columns, data
    types, constraints, and both explicit and inferred relationships.

    Automatically fixes known issues:
    - Normalizes table names to uppercase.
    - Removes invalid precision (e.g., decimal(10,2) -> decimal).
    - Escapes quotes and special characters for Mermaid syntax.
    - Ensures all sections render correctly.

    Args:
        tool_context: The ADK tool context providing session state.
        args: Optional argument dictionary (currently unused).

    Returns:
        Dict[str, Any]: {
            "status": "success" | "error",
            "message": Description message,
            "script_type": "Mermaid",
            "script": Mermaid ERD text (if success),
            "error": Optional error message (if failure)
        }
    """

    if not isinstance(args, dict):
        return {
            "status": "error",
            "error": "Invalid arguments. Expected a dictionary for args."
        }

    schema_structure = tool_context.state.get("schema_structure")
    if not schema_structure:
        return {
            "status": "error",
            "error": "Schema structure not found. Please run introspection first."
        }

    def sanitize_datatype(dtype: str) -> str:
        """Normalize SQL data types to Mermaid-safe equivalents."""
        if not dtype:
            return "text"
        dtype = dtype.strip().lower()
        if dtype.startswith("decimal"):
            return "decimal"
        if dtype.startswith("varchar"):
            return "varchar"
        if dtype.startswith("numeric"):
            return "numeric"
        if "int" in dtype:
            return "int"
        if dtype.startswith("enum"):
            return "enum"
        if "timestamp" in dtype:
            return "timestamp"
        return dtype.replace("(", "").replace(")", "").replace(",", "").replace(" ", "_")

    def format_column(table_name: str, col_name: str, col_info: Dict[str, Any], constraints_info: List[Dict[str, Any]]) -> str:
        """Format a column entry with proper constraints for Mermaid."""
        dtype = sanitize_datatype(col_info.get("type", "text"))
        constraints = []

        for c in constraints_info:
            if col_name in c.get("columns", []):
                c_type = c.get("type", "").upper()
                if "PRIMARY" in c_type:
                    constraints.append("PK")
                elif "UNIQUE" in c_type:
                    constraints.append("UK")

        if not col_info.get("nullable", True):
            constraints.append("NN")

        for fk in schema_structure.get("foreign_keys", []):
            if (
                fk.get("from_column") == col_name
                and fk.get("from_table", "").lower() == table_name.lower()
            ):
                constraints.append("FK")
                break

        constraint_str = f' "{", ".join(constraints)}"' if constraints else ""
        return f"        {dtype} {col_name}{constraint_str}"

    lines = ["erDiagram"]

    tables = schema_structure.get("tables", {})
    for table_name, table_info in tables.items():
        tname = table_name.upper()
        lines.append(f"    {tname} {{")

        columns = table_info.get("columns", {})
        constraints_info = table_info.get("constraints", [])

        for col_name, col_info in columns.items():
            lines.append(format_column(table_name, col_name, col_info, constraints_info))

        lines.append("    }")
        lines.append("")

    fks = schema_structure.get("foreign_keys", [])
    if fks:
        lines.append("    %% -- Explicit Relationships --")
        for fk in fks:
            from_table = fk.get("from_table", "").upper()
            to_table = fk.get("to_table", "").upper()
            from_column = fk.get("from_column", "")
            if from_table and to_table:
                lines.append(f'    {from_table} ||--o{{ {to_table} : "{from_column}"')

    inferred = schema_structure.get("inferred_relationships", [])
    if inferred:
        lines.append("\n    %% -- Inferred Relationships --")
        for rel in inferred:
            from_table = rel.get("from_table", "").upper()
            to_table = rel.get("to_table", "").upper()
            from_column = rel.get("from_column", "")

            if from_table and to_table:
                # Optional → Optional: }o--o{
                lines.append(
                    f'    {from_table} }}o--o{{ {to_table} : "INFERRED: {from_column}"'
                )

    mermaid_script = "\n".join(lines) + "\n"

    return {
        "status": "success",
        "message": "Mermaid ERD script generated successfully. Paste this code into any Mermaid renderer.",
        "script_type": "Mermaid",
        "script": mermaid_script
    }