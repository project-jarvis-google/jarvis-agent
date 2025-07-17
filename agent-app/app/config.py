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

import os
from dataclasses import dataclass

import google.auth

# To use AI Studio credentials:
# 1. Create a .env file in the /app directory with:
#    GOOGLE_GENAI_USE_VERTEXAI=FALSE
#    GOOGLE_API_KEY=PASTE_YOUR_ACTUAL_API_KEY_HERE
# 2. This will override the default Vertex AI configuration
_, project_id = google.auth.default()
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")
os.environ.setdefault("VERTEX_AI_RAG_CORPUS_ID", "7782220156096217088")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")
os.environ.setdefault("GCS_INSTRUMENTATION_BUCKET_NAME", "otel-instrumentation-test-bucket")
os.environ.setdefault("GCS_OTEL_COLLECTOR_BUCKET_NAME", "otel-agent")
os.environ.setdefault("GOOGLE_CLOUD_LOCATION_CORPUS", "us-central1")


# GOOGLE_GENAI_USE_VERTEXAI=1
# GOOGLE_CLOUD_PROJECT=agents-stg
# GOOGLE_CLOUD_LOCATION=us-central1
# GOOGLE_CLOUD_STORAGE_BUCKET=<YOUR_STORAGE_BUCKET>  # Only required for deployment on Agent Engine
# # VERTEX_AI_RAG_CORPUS_ID=6917529027641081856
# VERTEX_AI_RAG_CORPUS_ID=7782220156096217088
# GCS_INSTRUMENTATION_BUCKET_NAME=otel-instrumentation-test-bucket
# GCS_OTEL_COLLECTOR_BUCKET_NAME=otel-agent

@dataclass
class ResearchConfiguration:
    """Configuration for research-related models and parameters.

    Attributes:
        critic_model (str): Model for evaluation tasks.
        worker_model (str): Model for working/generation tasks.
        max_search_iterations (int): Maximum search iterations allowed.
    """

    critic_model: str = "gemini-2.5-pro"
    worker_model: str = "gemini-2.5-flash"
    max_search_iterations: int = 5


config = ResearchConfiguration()
