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

"""Opentelemetry Helper Agent: Answers user's query about the opentelemetry, or build opentelemetry collector configurations 
based on user input or return the java instrumented application gcs bucket url"""

from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool


from .sub_agents.otel_doc_rag_corpus_agent import otel_doc_rag_corpus_agent
from .sub_agents.otel_app_instrumentation_agent import otel_app_instrumentation_agent
from .sub_agents.otel_collector_config_agent import otel_collector_config_agent
from .config import config

MODEL = "gemini-2.5-flash"

otel_coordinator = LlmAgent(
    name="otel_coordinator",
    model=MODEL,
    description=(
        "Answers user's query about the opentelemetry, or create an opentelemetry collector starter pack with" \
        "configurations based on user input. If the user requests for it, return the java instrumented application gcs bucket url."
    ),
    instruction="You are a helpful agent who can answer user questions about Opentelemetry framework or create an " \
    "opentelemetry collector starter pack with configurations based on user input." \
    "If the user requests for it, return the java instrumented application gcs bucket url.",
    output_key="otel_coordinator_output",
    tools=[
        AgentTool(agent=otel_doc_rag_corpus_agent),
        AgentTool(agent=otel_app_instrumentation_agent),
        AgentTool(agent=otel_collector_config_agent),
    ],
)

root_agent = otel_coordinator