"""
Configuration settings for the Google Cloud Storage.
"""
import os

# Google Cloud Project Settings
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")  # Replace with your project ID
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")  # Default location for Vertex AI and GCS resources

# GCS Storage Settings
GCS_OTEL_COLLECTOR_BUCKET_NAME = os.environ.get("GCS_OTEL_COLLECTOR_BUCKET_NAME")
GCS_DEFAULT_STORAGE_CLASS = "STANDARD"
GCS_DEFAULT_LOCATION = "US"