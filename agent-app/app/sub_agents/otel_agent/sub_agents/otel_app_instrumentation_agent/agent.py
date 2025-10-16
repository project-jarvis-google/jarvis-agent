from google.adk.agents import Agent
from . import instrumentation_tools

MODEL = "gemini-2.5-flash"

otel_app_instrumentation_agent = Agent(
    name="otel_app_instrumentation_agent",
    model=MODEL,
    description=(
        "Agent for giving the gcs bucket url to user whenever they request for a java instrumented application."
    ),
    instruction=(
        """
        You are a helpful assistant that performs this function whenever user wants a java instrumented application.
        """
    ),
    tools=[instrumentation_tools.copy_gcs_folder],
)
