"""Detailed Architecture Design Agent:

This agent acts as a lead orchestrator for creating detailed software architectures.
It gathers initial requirements and then coordinates with a team of specialist sub-agents
to produce a comprehensive architecture design.
"""

from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool

from .config import MODEL
from .prompt import DETAILED_ARCHITECTURE_DESIGN_AGENT_PROMPT
from .sub_agents.component_design_agent import component_design_agent

detailed_architecture_design_agent = Agent(
    name="detailed_architecture_design_agent",
    model=MODEL,
    description="""
        The Detailed Architecture Parent Agent acts as a lead orchestrator in the architecture design process. 
        It begins by personally gathering the user's conceptual design and non-functional requirements (NFRs) to establish a strong foundation. 
        Once the initial requirements are clear, it coordinates a team of specialist sub-agents to delve into the specifics of the architecture, including: Component & Interaction Design, API & Data Flow Design and Deployment Architecture. 
        The agent's primary role is to synthesize the outputs from these specialist agents into a single, cohesive, and comprehensive detailed architecture. 
        It also manages the interactive design process, allowing users to ask questions, perform what-if analysis, and refine the design iteratively. 
        
        By orchestrating this entire workflow, the Detailed Architecture Parent Agent streamlines the creation of a complete and implementable architecture, from high-level concepts to detailed infrastructure and service design.
    """,
    instruction=DETAILED_ARCHITECTURE_DESIGN_AGENT_PROMPT,
    tools=[
        AgentTool(agent=component_design_agent),
    ],
)
