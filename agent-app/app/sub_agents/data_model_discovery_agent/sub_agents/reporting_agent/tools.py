import logging
from typing import Dict, Any, List
from google.adk.tools import ToolContext
import json
import yaml

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def generate_summary_report(tool_context: ToolContext, args: Dict[str, Any] = None) -> Dict[str, Any]:
    """Generates a high-level summary report of the database analysis."""
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

async def export_full_report(tool_context: ToolContext, args: Dict[str, Any]) -> Dict[str, Any]:
    """Exports the full schema structure and data profile as JSON or YAML."""
    schema_structure = tool_context.state.get("schema_structure")
    data_profile = tool_context.state.get("data_profile")
    format = args.get("format", "json").lower()

    if not schema_structure:
        return {"error": "Schema structure not found. Please run introspection first."}

    full_report_data = {
        "schema_structure": schema_structure,
        "data_profile": data_profile or "Not run",
    }

    try:
        if format == "yaml" or format == "yml":
            output = yaml.dump(full_report_data, indent=2, sort_keys=False)
            file_type = "YAML"
        else: # Default to JSON
            output = json.dumps(full_report_data, indent=2)
            file_type = "JSON"

        return {
            "status": "success",
            "message": f"Full report generated in {file_type} format. You can copy the content below.",
            "report_content": output,
            "format": file_type
        }
    except Exception as e:
        logger.error(f"Error generating {format} report: {e}", exc_info=True)
        return {"error": f"Failed to generate {format} report: {str(e)}"}

async def generate_erd_script(tool_context: ToolContext, args: Dict[str, Any]) -> Dict[str, Any]:
    """Generates a Mermaid script for an Entity Relationship Diagram."""
    schema_structure = tool_context.state.get("schema_structure")
    selected_schema = tool_context.state.get("selected_schema", "Schema")

    if not schema_structure:
        return {"error": "Schema structure not found. Please run introspection first."}

    tables = schema_structure.get("tables", {})
    fks = schema_structure.get("foreign_keys", [])
    inferred = schema_structure.get("inferred_relationships", [])

    mermaid_script = "erDiagram\n"

    # Add entities and attributes
    for table_name, table_info in tables.items():
        mermaid_script += f'    {table_name} {{\n'
        columns = table_info.get("columns", {})
        for col_name, col_info in columns.items():
            col_type = col_info.get("type", "")
            constraints = []
            for const in table_info.get("constraints", []):
                if const.get("columns") == col_name:
                    if const.get("type") == "PRIMARY KEY": constraints.append("PK")
                    if const.get("type") == "UNIQUE": constraints.append("UK")
            if not col_info.get("nullable"): constraints.append("NN")

            constraint_str = f" \"{', '.join(constraints)}\"" if constraints else ""
            mermaid_script += f'        {col_type} {col_name}{constraint_str}\n'
        mermaid_script += '    }\n'

    # Add relationships
    for fk in fks:
        from_table = fk.get("from_table")
        to_table = fk.get("to_table")
        from_column = fk.get("from_column")
        # label = fk.get("constraint_name", "")
        mermaid_script += f'    {from_table} ||--o{{ {to_table} : "{from_column}"\n'

    # Add inferred relationships
    if inferred:
        mermaid_script += "\n    %% Inferred Relationships\n"
        for rel in inferred:
             from_table = rel.get("from_table")
             to_table = rel.get("to_table")
             from_column = rel.get("from_column")
             mermaid_script += f'    {from_table} ..o{{ {to_table} : "Inferred: {from_column}"\n'

    return {
        "status": "success",
        "message": "Mermaid ERD script generated. You can render this in a Mermaid renderer.",
        "script_type": "Mermaid",
        "script": mermaid_script
    }