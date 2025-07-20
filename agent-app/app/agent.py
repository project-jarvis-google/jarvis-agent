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

"""Jarvis Agent: Answers user's query about the Presales and Delivery of theApplication Modernization, Application Development and Apigee as practice"""

from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
from .sub_agents.google_search_dummy_agent import google_search_dummy_agent
from .config import project_id, MODEL
from .prompt import ROOT_AGENT_PROMPT

system.out.println
root_agent = LlmAgent(
    name="jarvis_coordinator",
    model=MODEL,
    description=("Answers user's query about anything."),
    instruction=ROOT_AGENT_PROMPT,
    tools=[
        AgentTool(agent=google_search_dummy_agent),
    ],
)


