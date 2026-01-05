# root_agent.py

from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool

from .sub_agents.flow_definition_manager.flow_definition_agent import flow_definition_agent
from .sub_agents.interaction_manager.qa_agent import qa_agent
from .sub_agents.wireframe_manager.wireframe_agent import wireframe_agent
from .sub_agents.static_analysis_manager.static_analysis_agent import static_analysis_agent
from .sub_agents.dynamic_analysis_manager.dynamic_analysis_agent import dynamic_analysis_agent
from .sub_agents.reporting_manager.reporting_agent import reporting_agent
from .ux_analysis_root_prompt import ROOT_AGENT_PROMPT
from .tools.ux_analysis_tool import LogAnalysisToolWrapper


ux_analysis_root_agent = Agent(
    name="ux_analysis_root_agent",
    model="gemini-2.0-flash",
    description="UX Analysis Coordinator Agent that routes user requests to appropriate UX specialist sub-agents.",
    instruction=ROOT_AGENT_PROMPT,
    tools=[
        AgentTool(agent=flow_definition_agent),
        AgentTool(agent=reporting_agent),
        AgentTool(agent=static_analysis_agent),
        AgentTool(agent=qa_agent),
        AgentTool(agent=wireframe_agent),

        # Dynamic analysis chain:
        LogAnalysisToolWrapper(),             # 1) Normalize raw logs
        AgentTool(agent=dynamic_analysis_agent),  # 2) Analyze normalized JSON (argument name = 'request')
    ],
)
