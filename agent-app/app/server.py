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
"""Agent App"""

import os

import google.auth
from fastapi import FastAPI, File, HTTPException, UploadFile
from google.adk.cli.fast_api import get_fast_api_app
from google.api_core import exceptions
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider, export

from app.utils.gcs import create_bucket_if_not_exists, upload_file_to_gcs
from app.utils.tracing import CloudTraceLoggingSpanExporter

_, project_id = google.auth.default()
allow_origins = (
    os.getenv("ALLOW_ORIGINS", "*").split(",") if os.getenv("ALLOW_ORIGINS") else ["*"]
)

bucket_name = f"{project_id}-agent-app-logs-data"
bucket_uri = "gs://" + bucket_name
create_bucket_if_not_exists(
    bucket_name=bucket_name, project=project_id, location="us-central1"
)

provider = TracerProvider()
processor = export.BatchSpanProcessor(CloudTraceLoggingSpanExporter())
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

AGENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# AlloyDB session configuration
db_user = os.environ.get("DB_USER", "postgres")
db_name = os.environ.get("DB_NAME", "postgres")
db_pass = os.environ.get("DB_PASS")
db_host = os.environ.get("DB_HOST")

# Set session_service_uri if database credentials are available
SESSION_SERVICE_URI = None
if db_host and db_pass:
    SESSION_SERVICE_URI = f"postgresql://{db_user}:{db_pass}@{db_host}:5432/{db_name}"
app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    web=True,
    artifact_service_uri=bucket_uri,
    allow_origins=allow_origins,
    session_service_uri=SESSION_SERVICE_URI,
)
app.title = "jarvis-app"
app.description = "API for interacting with the Agent jarvis-app"


@app.post("/upload-file")
async def upload_file_to_gcs_bucket(file: UploadFile = File(...)):
    """
    Uploads a file to the configured GCS bucket.
    """
    if not bucket_name:
        raise HTTPException(
            status_code=500, detail=f"{bucket_name} gcs bucket doesn't exist"
        )
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file name provided.")

    try:
        upload_file_to_gcs(
            gcs_bucket_name=bucket_name,
            gcs_file_name=file.filename,
            file_obj=file.file,
            file_content_type=file.content_type,
        )
        return {
            "gsutil_uri": bucket_uri + "/" + file.filename,
            "content_type": file.content_type,
        }
    except exceptions.GoogleAPICallError as e:
        raise HTTPException(
            status_code=500, detail=f"File upload failed: {e.reason}"
        ) from e


# Main execution
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
