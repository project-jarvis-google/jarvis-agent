from google.adk.agents import ParallelAgent

from .sub_agents.database_analyzer_agent import database_analyzer_agent
from .sub_agents.framework_analyzer_agent import framework_analyzer_agent
from .sub_agents.language_identifier_agent import language_identifier_agent

MODEL = "gemini-2.5-flash"

parallel_codebase_analyzer_agent = ParallelAgent(
    name="parallel_codebase_analyzer_agent",
    description=("""Runs parallel agents to perform codebase analysis"""),
    sub_agents=[
        language_identifier_agent,
        framework_analyzer_agent,
        database_analyzer_agent,
    ],
)
