import io
import logging

logger = logging.getLogger(__name__)

from google.adk.tools import ToolContext

async def load_application_csv_artifact(tool_context: ToolContext):
    logger.info("In load_application_csv_artifact")
    
    app_data = await tool_context.load_artifact("sample_app.csv")
    if app_data is not None:
        logger.info(f"app data => {(app_data.inline_data.data).decode('utf-8')}")
        tool_context.state["app_data"] = (app_data.inline_data.data).decode('utf-8')
    return app_data

async def load_server_csv_artifact(tool_context: ToolContext):
    logger.info("In load_server_csv_artifact")
    
    server_data = await tool_context.load_artifact("sample_server.csv")
    if server_data is not None:
        logger.info(f"server data => {(server_data.inline_data.data).decode('utf-8')}")
        tool_context.state["server_data"] = (server_data.inline_data.data).decode('utf-8')