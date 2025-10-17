from datetime import datetime
from typing import Any

from google.adk.tools import ToolContext
from google.api_core.exceptions import GoogleAPIError
from google.cloud import storage

from .gcs_config import GCS_INSTRUMENTATION_BUCKET_NAME, PROJECT_ID


def copy_gcs_folder(
    tool_context: ToolContext,  # Included for signature similarity, not used in logic
    # source_bucket_name: str,
    # source_folder_prefix: str,
    # destination_bucket_name: str,
    # destination_folder_prefix: str
) -> dict[str, Any]:
    """
    When user says they want a java instrumented application, perform this function and return the results.

    Args:
        tool_context: The tool context for ADK (not used in this function's logic).

    Returns:
        A dictionary containing the result of the copy operation.
    """
    # Ensure prefixes end with a slash if they are not empty for consistent path handling

    source_bucket_name = GCS_INSTRUMENTATION_BUCKET_NAME
    destination_bucket_name = GCS_INSTRUMENTATION_BUCKET_NAME

    source_folder_prefix = "java-instrumented-app/"
    destination_folder_prefix = (
        datetime.now().strftime("%d%m%Y%H%M%S") + "-java-instrumented-app-2/"
    )

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
        blob_list = list(blobs)  # Consume the iterator into a list

        if not blob_list:
            return {
                "status": "success",
                "source_bucket": source_bucket_name,
                "source_folder": source_folder_prefix,
                "destination_bucket": destination_bucket_name,
                "destination_folder": destination_folder_prefix,
                "copied_count": 0,
                "message": f"No files found with prefix '{source_folder_prefix}' in bucket '{source_bucket_name}'. No files copied.",
            }

        for blob in blob_list:
            # Calculate the new blob name in the destination folder
            # Ensure we only take the part of the name *after* the source prefix
            relative_path = blob.name[len(source_folder_prefix) :]
            destination_blob_name = destination_folder_prefix + relative_path

            try:
                # Copy the blob
                source_bucket.copy_blob(blob, destination_bucket, destination_blob_name)
                copied_files.append(blob.name)
            except GoogleAPIError as e:
                failed_files.append({"file": blob.name, "error": str(e)})
            except Exception as e:
                failed_files.append(
                    {"file": blob.name, "error": f"Unexpected error: {e!s}"}
                )

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
                "message": f"Copy operation completed with {len(copied_files)} successes and {len(failed_files)} failures out of {total_files_processed} files found.",
            }
        else:
            return {
                "status": "success",
                "source_bucket": source_bucket_name,
                "source_folder": source_folder_prefix,
                "destination_bucket": destination_bucket_name,
                "destination_folder": destination_folder_prefix,
                "copied_count": len(copied_files),
                "message": f"Successfully copied {len(copied_files)} files from '{source_bucket_name}/{source_folder_prefix}' to '{destination_bucket_name}/{destination_folder_prefix}'.",
            }

    except GoogleAPIError as e:
        # This catches errors during client init, get_bucket, or initial list_blobs failure
        return {
            "status": "error",
            "error_message": str(e),
            "message": f"Failed to initialize client, get buckets, or list files: {e!s}",
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e),
            "message": f"An unexpected error occurred during setup or listing: {e!s}",
        }
