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

import logging
from typing import IO

import google.cloud.storage as storage
from google.api_core import exceptions


def create_bucket_if_not_exists(bucket_name: str, project: str, location: str) -> None:
    """Creates a new bucket if it doesn't already exist.

    Args:
        bucket_name: Name of the bucket to create
        project: Google Cloud project ID
        location: Location to create the bucket in (defaults to us-central1)
    """
    storage_client = storage.Client(project=project)

    if bucket_name.startswith("gs://"):
        bucket_name = bucket_name[5:]
    try:
        storage_client.get_bucket(bucket_name)
        logging.info("Bucket %s already exists", bucket_name)
    except exceptions.NotFound:
        bucket = storage_client.create_bucket(
            bucket_name,
            location=location,
            project=project,
        )
        logging.info("Created bucket %s in %s", bucket.name, bucket.location)


def upload_str_to_gcs_bucket(
    gcs_bucket_name: str, gcs_file_name: str, file_path: str, file_content_type: str
) -> bool:
    """Uploads a file to a Google Cloud Storage bucket.

    Args:
        gcs_bucket_name: The name of the GCS bucket.
        gcs_file_name: The desired name of the file in the bucket.
        file_path: The local path to the file to upload.
        file_content_type: The content type of the file (e.g., 'application/pdf').

    Returns:
        True if the upload was successful, False otherwise.
    """
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(gcs_bucket_name)
        blob = bucket.blob(gcs_file_name)
        logging.info(
            "Uploading %s to gs://%s/%s...", file_path, gcs_bucket_name, gcs_file_name
        )
        blob.upload_from_filename(file_path, content_type=file_content_type)
        logging.info(
            "Successfully uploaded to gs://%s/%s", gcs_bucket_name, gcs_file_name
        )
        return True
    except exceptions.GoogleAPICallError as e:
        logging.error(
            "Failed to upload %s to GCS bucket %s: %s",
            file_path,
            gcs_bucket_name,
            e,
            exc_info=True,
        )
        return False


def upload_file_to_gcs(
    gcs_bucket_name: str,
    gcs_file_name: str,
    file_obj: IO,
    file_content_type: str | None,
) -> None:
    """Uploads a file object to a Google Cloud Storage bucket.

    Args:
        gcs_bucket_name: The name of the GCS bucket.
        gcs_file_name: The desired name of the file in the bucket.
        file_obj: The file-like object to upload.
        file_content_type: The content type of the file (e.g., 'application/pdf').

    Raises:
        google.api_core.exceptions.GoogleAPICallError: If the upload fails.
    """
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(gcs_bucket_name)
        blob = bucket.blob(gcs_file_name)
        logging.info(
            "Uploading %s to gs://%s/%s...",
            gcs_file_name,
            gcs_bucket_name,
            gcs_file_name,
        )
        blob.upload_from_file(file_obj, content_type=file_content_type)
        logging.info(
            "Successfully uploaded to gs://%s/%s", gcs_bucket_name, gcs_file_name
        )
    except exceptions.GoogleAPICallError as e:
        logging.error(
            "Failed to upload %s to GCS bucket %s: %s",
            gcs_file_name,
            gcs_bucket_name,
            e,
            exc_info=True,
        )
        raise
