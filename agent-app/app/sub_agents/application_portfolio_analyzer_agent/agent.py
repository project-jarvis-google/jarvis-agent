from google.adk.agents import LlmAgent

from .prompt import APPLICATION_PORTFOLIO_ANALYZER_PROMPT

from .sub_agents.csv_data_analyzer import csv_data_analyzer_agent

MODEL = "gemini-2.5-flash"

application_portfolio_analyzer = LlmAgent(
    name="application_portfolio_analyzer",
    model=MODEL,
    description=(
    """ 
        Analyzes the application portfolio csv file and provides useful insights.
    """
    ),
    instruction=APPLICATION_PORTFOLIO_ANALYZER_PROMPT,
    # instruction=APPLICATION_PORTFOLIO_ANALYZER_PROMPT_NEW,
    # tools=[AgentTool(csv_data_analyzer_agent)]
    sub_agents=[csv_data_analyzer_agent]
    # output_key="application_portfolio_analyzer_output",
)