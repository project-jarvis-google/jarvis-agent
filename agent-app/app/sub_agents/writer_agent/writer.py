import google.genai.types as types
from google.adk.agents.callback_context import CallbackContext # Or ToolContext
from google.adk.models import LlmResponse

async def save_generated_report_py(text: str):
    print(text)