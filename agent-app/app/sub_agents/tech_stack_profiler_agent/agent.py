"""Tech Stack Profiler Agent: Profiles source code directory or git repository and provides
detailed report of breakdown of programming languages, list of frameworks, databases and it's
configurations, deployment strategy etc"""

from google.adk.agents import LlmAgent

from .prompt import TECH_STACK_PROFILER_PROMPT
from .sub_agents.gcs_upload_tech_profile_pdf_report_agent import (
    gcs_upload_tech_profile_pdf_report_agent,
)
from .sub_agents.tech_stack_seq_agent import tech_stack_seq_agent

MODEL = "gemini-2.5-flash"

tech_stack_profiler = LlmAgent(
    name="tech_stack_profiler",
    model=MODEL,
    description=(
        """ 
        Profiles source code base or git repository and provides 
        detailed report of breakdown of programming languages, list of frameworks, databases 
        and it's  configurations etc. Also provides an option to convert the report to pdf
        format and uploads it to a gcs bucket. Then sends the link of the gcs location to the user
    """
    ),
    instruction=TECH_STACK_PROFILER_PROMPT,
    # output_key="tech_stack_profiler_output",
    sub_agents=[tech_stack_seq_agent, gcs_upload_tech_profile_pdf_report_agent],
)
