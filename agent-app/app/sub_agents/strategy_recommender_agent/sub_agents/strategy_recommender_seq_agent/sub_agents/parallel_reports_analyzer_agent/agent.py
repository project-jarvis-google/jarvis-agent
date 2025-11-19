from google.adk.agents import ParallelAgent
from .sub_agents.discovery_report_strategy_recommender_agent import discovery_report_strategy_recommender_agent
from .sub_agents.tech_stack_analyzer_agent import tech_stack_analyzer_agent

MODEL = "gemini-2.5-flash"

parallel_reports_analyzer_agent = ParallelAgent(
    name="parallel_reports_analyzer_agent",
    description=(
        """Runs parallel agents to do analysis on the extracted summary from the previous agent for Discovery report"""
    ),
   sub_agents=[
       discovery_report_strategy_recommender_agent,
       tech_stack_analyzer_agent # Add the new tech stack analyzer agent here
   ]
)
