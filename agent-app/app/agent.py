# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Jarvis Agent: Answers user's query about the Presales 
and Delivery of theApplication Modernization, Application Development 
and Apigee as practice
"""

from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
from .sub_agents.google_search_dummy_agent import google_search_dummy_agent
from .sub_agents.common_utility_agent.mosaic_rag_agent_presales import mosaic_rag_agent_presales
from .sub_agents.tech_stack_profiler_agent import tech_stack_profiler
from .sub_agents.discovery_interview_agent import discovery_architect_agent
from .sub_agents.compliance_and_security_baseline_agent import compliance_agent
from .config import MODEL
from .prompt import ROOT_AGENT_PROMPT
from .tools import transfer_to_discovery_agent_tool, transfer_to_capability_mapper_agent_tool,transfer_to_strategy_recommender_agent_tool
from .sub_agents.recommendation_agent import recommendation_agent
from .sub_agents.strategy_recommender_agent import strategy_recommender_agent
from .sub_agents.infrastructure_scanner_agent import infra_scanner_agent
from .sub_agents.capability_mapper_agent import capability_mapper_agent
from .sub_agents.otel_agent import otel_coordinator

root_agent = LlmAgent(
    model=MODEL, # A fast model is good for simple routing
    name="jarvis_coordinator",
    instruction=ROOT_AGENT_PROMPT,
    tools=[
        AgentTool(agent=google_search_dummy_agent),
        AgentTool(agent=mosaic_rag_agent_presales),
        AgentTool(agent=tech_stack_profiler),
        AgentTool(agent=infra_scanner_agent),
        transfer_to_discovery_agent_tool,
        transfer_to_capability_mapper_agent_tool,
        transfer_to_strategy_recommender_agent_tool,
        AgentTool(agent=compliance_agent),
        AgentTool(agent=otel_coordinator)
    ],
  # -- This is the key step to link the agents ---
     sub_agents=[discovery_architect_agent, recommendation_agent, capability_mapper_agent, strategy_recommender_agent]
)