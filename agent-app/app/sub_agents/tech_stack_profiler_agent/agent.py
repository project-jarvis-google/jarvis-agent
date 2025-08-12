"""Tech Stack Profiler Agent: Profiles source code directory or git repository and provides 
detailed report of breakdown of programming languages, list of frameworks, databases and it's 
configurations, deployment strategy etc"""

import os
import logging
from google.adk.agents import LlmAgent

from .sub_agents.tech_stack_seq_agent import tech_stack_seq_agent
from .prompt import TECH_STACK_PROFILER_PROMPT


MODEL = "gemini-2.5-flash"

tech_stack_profiler = LlmAgent(
    name="tech_stack_profiler",
    model=MODEL,
    description=(
    """ 
        Profiles source code base or git repository and provides 
        detailed report of breakdown of programming languages, list of frameworks, databases 
        and it's  configurations, deployment strategy etc.
        Ask user for the link of the git repository of the source code and also mention 
        that if the repository is private, they also need to provide the access token.
    """
    ),
    instruction=TECH_STACK_PROFILER_PROMPT,
    output_key="tech_stack_profiler_output",
    sub_agents=[tech_stack_seq_agent]
)