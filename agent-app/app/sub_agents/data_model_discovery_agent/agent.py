from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents.readonly_context import ReadonlyContext
from .sub_agents.database_cred_agent.agent import database_cred_agent
from .sub_agents.schema_introspection_agent.agent import schema_introspection_agent
from .sub_agents.qa_agent.agent import qa_agent
from .sub_agents.data_profiling_agent.agent import data_profiling_agent
from .sub_agents.reporting_agent.agent import reporting_agent

import logging
import json

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def root_agent_instruction(ctx: ReadonlyContext) -> str:
    """Dynamically builds the Root Agent's instruction based on session state."""
    selected_schema = ctx.state.get("selected_schema")
    db_connection = ctx.state.get("db_connection")
    available_schemas = ctx.state.get("available_schemas")
    schema_structure = ctx.state.get("schema_structure")
    data_profile = ctx.state.get("data_profile")

    base_instruction = """
    ## Role
    You are the **Root Agent** responsible for coordinating sub-agents to perform database discovery, introspection, profiling, and reporting tasks.
    You manage the overall flow, handle user selections, and determine which sub-agent should be called.

    ## Sub-Agent Hierarchy
    You have the following sub-agents under your control:
    1.  **database_cred_agent**: Collects and validates DB credentials, lists schemas.
    2.  **schema_introspection_agent**: Discovers schema details, constraints, and relationships.
    3.  **data_profiling_agent**: Analyzes data quality within the selected schema.
    4.  **reporting_agent**: Generates summaries, exports data, and creates schema diagrams.
    5.  **qa_agent**: Answers questions about the discovered schema and data profile.
    ---
    """

    if not db_connection or db_connection.get("status") != "connected":
        return base_instruction + """
    **Current Task:** The database is not connected.
    -   Greet the user and explain your purpose.
    -   If the user indicates they want to analyze a database, you MUST call the `database_cred_agent` to start the connection process.
    Example Response: "Welcome! I'm your Data Discovery Agent. I can help you connect to, understand, profile, and report on your legacy databases. To begin, I need to connect to your database."
    User Intent: "I want to analyze my DB" -> Call `database_cred_agent`.
        """
    elif available_schemas and not selected_schema:
        return base_instruction + """
    **Current Task:** The user has been presented with a list of available schemas by the `database_cred_agent`. Their current input is expected to be the name of the schema they wish to analyze.

    1.  Consider the user's entire input as the desired schema name.
    2.  You MUST call the `schema_introspection_agent`. Pass the user's input as the primary query to this sub-agent. The `schema_introspection_agent` is designed to take this input as the schema name for its operations.
        - Example AgentTool Call: `schema_introspection_agent(user_input)`
    3.  The `schema_introspection_agent` will handle storing the selected schema and fetching the details. Await its response.
        """
    elif selected_schema and schema_structure:
        profile_status = "Completed" if data_profile else "Not Yet Run"
        return base_instruction + f"""
    **Current Context:** The database is connected. The schema '{selected_schema}' has been successfully introspected.
    Data Quality Profile Status: {profile_status}

    **Task Delegation:** Based on the user's request, delegate to the appropriate sub-agent:

    -   **"Profile Data"**, **"Data Quality"**, **"Run profiling"**:
        Call `data_profiling_agent`.
        - Example: `data_profiling_agent()`

    -   **"Generate Report"**, **"Export"**, **"Diagram"**, **"Summary"**, **"ERD"**, **"JSON"**, **"YAML"**, **"Mermaid"**:
        Call `reporting_agent` and pass the user's query.
        - Example: `reporting_agent(user_input)`

    -   **ANY other questions** about the tables, columns, constraints, relationships, views, indexes, anomalies within the '{selected_schema}' schema, or about the data profile results:
        Call `qa_agent` and pass the user's question as the query.
        - Example: `qa_agent(user_question)`

    If the user's intent is unclear, ask for clarification. You can remind them of the available actions.
        """
    elif selected_schema and not schema_structure:
         return base_instruction + f"""
    **Current Context:** The schema '{selected_schema}' was selected, but the introspection data is missing or incomplete.
    - Recall `schema_introspection_agent` and pass the schema name '{selected_schema}' as the input to it to ensure the structure is loaded.
    - Example AgentTool Call: `schema_introspection_agent("{selected_schema}")`
         """
    else: # Should ideally not be reached if states are managed well
        return base_instruction + """
    **Current Task:** Determine the next step based on the conversation history and session state. If unsure, ask the user for clarification.
        """

data_model_discovery_agent = LlmAgent(
    model='gemini-2.5-flash',
    name='data_model_discovery_agent',
    description=(
        "A helpful root agent that orchestrates sub-agents to introspect and profile legacy databases."
    ),
    instruction=root_agent_instruction,
    sub_agents=[
        database_cred_agent,
        schema_introspection_agent,
        qa_agent,
        data_profiling_agent,
        reporting_agent,
    ]
)
