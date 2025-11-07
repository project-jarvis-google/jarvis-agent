from google.adk.agents import SequentialAgent

from .sub_agents.parallel_codebase_analyzer_agent import (
    parallel_codebase_analyzer_agent,
)
from .sub_agents.report_generator_agent import report_generator_agent
from .sub_agents.rule_extraction_runner_agent import rule_extraction_runner_agent
from .sub_agents.source_code_staging_agent import source_code_staging_agent

MODEL = "gemini-1.5-flash"

business_logic_seq_agent = SequentialAgent(
    name="business_logic_seq_agent",
    description=(
        """Executes a sequence of repository preparation, code analysis and report building"""
    ),
    sub_agents=[
        source_code_staging_agent,
        parallel_codebase_analyzer_agent,
        rule_extraction_runner_agent,
        report_generator_agent,
    ],
)
