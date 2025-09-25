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
Strategy Recommender Agent: Answers user's query about the GCP Migration/Modernization Strategy Recommendations 
against the discovered application characterstics and business goals.
Provides Strategy Recommendation Report evaluating various "Rs" and a data-driven justification for the chosen strategy
"""

import os
import logging
from google.adk.agents import LlmAgent
from .prompt import STRATEGY_RECOMMENDER_PROMPT
from .sub_agents.strategy_recommender_seq_agent import strategy_recommender_seq_agent
from google.adk.agents import SequentialAgent
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.artifacts import InMemoryArtifactService 
from google.adk.sessions import InMemorySessionService

MODEL = "gemini-2.5-flash"

strategy_recommender_agent = LlmAgent(
    name="strategy_recommender_agent",
    model=MODEL,
    description=(
    """ 
        You are a helpful assistant design to scan the input Discovery Report and evaluates the discovered application characterstics like summary, pain points
        and business outcomes against various "Rs"(rehost, replatform, refactor, re-architect, rebuild, replace, retire) and
        provide the recommended strategy considering the Discovery Report provided as input.
        Ask user for the Discovery Report as input to provide a data-driven justification for the chosen strategy.
    """
    ),
    instruction=STRATEGY_RECOMMENDER_PROMPT,
    output_key="strategy_recommender_output",
    sub_agents=[strategy_recommender_seq_agent]
)

# Instantiate the desired artifact service
artifact_service = InMemoryArtifactService()
session_service = InMemorySessionService()

runner = Runner(
    agent=strategy_recommender_agent,
    app_name="strategy_recommender_agent",
    session_service=session_service,
    artifact_service=artifact_service # Provide the service instance here
)