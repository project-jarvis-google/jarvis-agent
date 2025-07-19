from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from ..otel_doc_rag_corpus_agent import otel_doc_rag_corpus_agent

from . import prompt

from google.cloud import storage
from google.api_core.exceptions import GoogleAPIError
from google.adk.tools import ToolContext
from datetime import datetime

from typing import Dict, Optional, Any

MODEL = "gemini-2.5-pro"

from .gcs_config import (
    PROJECT_ID,
    GCS_OTEL_COLLECTOR_BUCKET_NAME
)    

def create_starter_pack( 
    tool_context: ToolContext, # Included for signature similarity, not used in logic
    otel_config_str: str,
    note_str: str
    # source_bucket_name: str,
    # source_folder_prefix: str,
    # destination_bucket_name: str,
    # destination_folder_prefix: str
) -> Dict[str, Any]:
    """
    Invoke this function when opentelemetry configurations need to be created. This function makes a copy of a folder
    in the same GCS bucket and then calls the upload_file_to_gcs function to upload the config string as a yaml file.

    Args:
        tool_context: The tool context for ADK (not used in this function's logic).
        otel_config_str: The opentelemetry collector configurations stored in string format
        note_str: The additional notes about the components of the collector configurations

    Returns:
        A dictionary containing the result of the copy operation with the GCS folder url.
    """
    # Ensure prefixes end with a slash if they are not empty for consistent path handling

    source_bucket_name = GCS_OTEL_COLLECTOR_BUCKET_NAME
    destination_bucket_name = GCS_OTEL_COLLECTOR_BUCKET_NAME

    source_folder_prefix = "otel-collector-base-files/"
    destination_folder_prefix = "user-generated-collector-configs/" + datetime.now().strftime("%d%m%Y%H%M%S") + "-otel-collector/"

    try:
        client = storage.Client(project=PROJECT_ID)

        # Get source and destination buckets - this will raise GoogleAPIError if they don't exist
        source_bucket = client.get_bucket(source_bucket_name)
        destination_bucket = client.get_bucket(destination_bucket_name)

        copied_files = []
        failed_files = []

        # List blobs in the source folder (prefix)
        blobs = source_bucket.list_blobs(prefix=source_folder_prefix)

        # Check if any blobs were found
        # Use a list comprehension or generator expression to check without consuming the iterator
        # Or consume and re-list if needed. Consuming and re-listing is simpler here.
        blob_list = list(blobs) # Consume the iterator into a list

        if not blob_list:
             return {
                "status": "success",
                "source_bucket": source_bucket_name,
                "source_folder": source_folder_prefix,
                "destination_bucket": destination_bucket_name,
                "destination_folder": destination_folder_prefix,
                "copied_count": 0,
                "message": f"No files found with prefix '{source_folder_prefix}' in bucket '{source_bucket_name}'. No files copied."
            }

        for blob in blob_list:
            # Calculate the new blob name in the destination folder
            # Ensure we only take the part of the name *after* the source prefix
            relative_path = blob.name[len(source_folder_prefix):]
            destination_blob_name = destination_folder_prefix + relative_path

            try:
                # Copy the blob
                source_bucket.copy_blob(
                    blob, destination_bucket, destination_blob_name
                )
                copied_files.append(blob.name)
            except GoogleAPIError as e:
                failed_files.append({"file": blob.name, "error": str(e)})
            except Exception as e:
                failed_files.append({"file": blob.name, "error": f"Unexpected error: {str(e)}"})

        total_files_processed = len(copied_files) + len(failed_files)

        if failed_files:
             return {
                "status": "partial_success" if copied_files else "error",
                "source_bucket": source_bucket_name,
                "source_folder": source_folder_prefix,
                "destination_bucket": destination_bucket_name,
                "destination_folder": destination_folder_prefix,
                "copied_count": len(copied_files),
                "failed_count": len(failed_files),
                "failed_files": failed_files,
                "message": f"Copy operation completed with {len(copied_files)} successes and {len(failed_files)} failures out of {total_files_processed} files found."
            }
        else:
            upload_file_to_gcs(tool_context, otel_config_str, note_str, destination_folder_prefix)
            return {
                "status": "success",
                "source_bucket": source_bucket_name,
                "source_folder": source_folder_prefix,
                "destination_bucket": destination_bucket_name,
                "destination_folder": destination_folder_prefix,
                "copied_count": len(copied_files),
                "message": f"Successfully created otel config at: gs://{source_bucket_name}+{destination_folder_prefix}."
            }

    except GoogleAPIError as e:
        # This catches errors during client init, get_bucket, or initial list_blobs failure
        return {
            "status": "error",
            "error_message": str(e),
            "message": f"Failed to initialize client, get buckets, or list files: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e),
            "message": f"An unexpected error occurred during setup or listing: {str(e)}"
        }

def upload_file_to_gcs(
    tool_context: ToolContext, # Included for signature similarity, not used in logic
    otel_config_str: str,
    note_str: str,
    destination_blob_name: str,
) -> Dict[str, Any]:
    
    """Uploads a string (expected to be YAML) as a file to a GCS bucket.

    Args:
        otel_config_str (str): The string content to upload (should be valid YAML).
        note_str : The additional notes about the components of the collector configurations

    Returns:
        A dictionary containing the result of the copy operation.
    """
    try:
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(GCS_OTEL_COLLECTOR_BUCKET_NAME)
        blob = bucket.blob(destination_blob_name + "otelcol-deployment/otel-config.yaml")

        # Upload the string directly
        blob.upload_from_string(otel_config_str, content_type='application/x-yaml')

        blob = bucket.blob(destination_blob_name + "otelcol-deployment/README.md")
        blob.upload_from_string(note_str, content_type='test/markdown')

        print(f"Otel config data uploaded as {destination_blob_name} to bucket {GCS_OTEL_COLLECTOR_BUCKET_NAME}.")

        return {
            "status": "success",
            "message": f"Otel config data uploaded as {destination_blob_name} to bucket {GCS_OTEL_COLLECTOR_BUCKET_NAME}."
        }

    except GoogleAPIError as e:
        return {
            "status": "error",
            "error_message": str(e),
            "message": f"Failed to upload file: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e),
            "message": f"An unexpected error occurred: {str(e)}"
        }

otel_collector_config_agent = Agent(
    name="otel_collector_config_agent",
    model=MODEL,
    description=(
        """
            Agent for creating opentelemetry starter pack with custom configurations provided by user. 
            The agent displays the config to the user and also uploads it to a GCS bucket
        """
    ),
    instruction=prompt.OTEL_COLLECTOR_CONFIG_PROMPT,
    tools=[AgentTool(agent=otel_doc_rag_corpus_agent), create_starter_pack]
)