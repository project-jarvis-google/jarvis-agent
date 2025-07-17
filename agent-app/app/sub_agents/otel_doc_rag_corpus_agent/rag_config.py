"""
Configuration settings for the Vertex AI RAG engine.
"""
import os
import google.auth

_, project_id = google.auth.default()
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "us-central1")
os.environ.setdefault("VERTEX_AI_RAG_CORPUS_ID", "7782220156096217088")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")
os.environ.setdefault("GCS_INSTRUMENTATION_BUCKET_NAME", "otel-instrumentation-test-bucket")
os.environ.setdefault("GCS_OTEL_COLLECTOR_BUCKET_NAME", "otel-agent")
os.environ.setdefault("GOOGLE_CLOUD_LOCATION_CORPUS", "us-central1")

# Google Cloud Project Settings
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")  # Replace with your project ID
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION_CORPUS", "us-central1")  # Default location for Vertex AI and GCS resources

# RAG Corpus Settings
CORPUS_ID = os.environ.get("VERTEX_AI_RAG_CORPUS_ID")  # Replace with your project ID
RAG_DEFAULT_TOP_K = 5  # Default number of results for single corpus query
RAG_DEFAULT_VECTOR_DISTANCE_THRESHOLD = 0.5