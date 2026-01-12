import json
from decimal import Decimal

from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents.readonly_context import ReadonlyContext

from app.config import MODEL


def json_encoder_default(obj):
    if isinstance(obj, Decimal):
        return str(obj)
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")


def qa_agent_instruction(ctx: ReadonlyContext) -> str:
    """Builds the QA agent's instruction for schema and data profiling queries."""

    schema_structure = ctx.state.get("schema_structure")
    data_profile = ctx.state.get("data_profile")
    selected_schema = ctx.state.get("selected_schema", "the selected schema")

    # Handle missing schema
    if not schema_structure:
        return f"""
        ### Role
        You are a Database Schema & Data Profile Q&A Assistant. 

        ### Task
        I currently do not have the schema details for '{selected_schema}'.
        To answer schema-related questions, the schema must be introspected first.
        You might say: "I don't have the schema details yet. Would you like me to run schema discovery first?"
        """

    try:
        schema_json = json.dumps(
            schema_structure, indent=2, default=json_encoder_default
        )
    except Exception as e:
        schema_json = f"Error serializing schema structure: {e}"

    # Handle data profiling
    profile_message = ""
    if data_profile:
        try:
            # Only display human-readable summary, not raw session variables
            profile_summary = {
                "Nullability": data_profile.get("nullability", "Not available"),
                "Cardinality": data_profile.get("cardinality", "Not available"),
                "Orphan Records": data_profile.get("orphan_records", "Not available"),
                "Type Anomalies": data_profile.get("type_anomalies", "Not available"),
            }
            profile_message = json.dumps(
                profile_summary, indent=2, default=json_encoder_default
            )
        except Exception:
            profile_message = (
                "Data profiling results exist but could not be summarized."
            )
    else:
        profile_message = (
            "Data profiling has not been run yet. "
            "If you would like, I can run data profiling on this database "
            "(sampling up to 10,000 rows) and provide a summary of key findings."
        )

    return f"""
    ### Role
    You are a Database Schema & Data Profile Q&A Assistant. Your goal is to answer user questions 
    about the database schema and data profiling in a conversational, human-friendly way.

    ### Schema Context for '{selected_schema}'
    The schema has been discovered and includes tables, columns, constraints, and relationships.
    ```json
    {schema_json}
    ```

    ### Data Profiling Context for '{selected_schema}'
    {profile_message}

    ### Instructions
    1. Answer questions only based on the provided schema structure and data profiling information.
    2. Avoid exposing raw internal session variables or empty lists directly. Answer conversationally.
    3. If data profiling has not been run and the user asks about it, politely suggest running profiling on up to 10,000 rows.
    4. If the user asks to generate a **Mermaid diagram** of the schema or to **export the schema structure as a JSON response**, transfer the request to the `reporting_agent` by calling:
       `transfer_to_agent(reporting_agent, query)`
    5. Use tables for lists when helpful.
    6. If a question is outside your scope, guide the user to the appropriate agent instead.

    ### Examples
    * "List all tables": List tables from the schema.
    * "Columns in 'customers'?": List columns for that table.
    * "FKs for 'orders'?": List foreign keys involving that table.
    * "Which columns have high nulls?": Refer to data profiling nullability.
    * "Are there orphan records?": Summarize orphan records in a human-friendly way.
    * "Any type anomalies?": List columns with type inconsistencies in plain language.
    * "Generate a Mermaid diagram of the schema": Transfer to `reporting_agent`.
    * "Export the schema as JSON": Transfer to `reporting_agent`.

    Always respond in clear, human-readable sentences. If profiling data is missing, offer to run profiling on a sample of up to 10,000 rows to provide a summary.
    """


qa_agent = LlmAgent(
    model=MODEL,
    name="qa_agent",
    description="Answers natural language questions about the discovered database schema structure and data profiling results.",
    instruction=qa_agent_instruction,
    tools=[],
)
