# tools.py
import csv
import datetime
import io
import logging
import os
import tempfile

import numpy as np
from google.adk.tools import FunctionTool
from google.cloud import storage
from scipy.spatial.distance import cdist
from vertexai.language_models import TextEmbeddingModel

# --- Setup Logging and Models ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize this once to be reused by tools
embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")


def _get_gcs_client():
    """Initializes and returns a Google Cloud Storage client."""
    return storage.Client()


# --- Tool 1: Capability to Application Mapping (Scenario 2) ---


def map_capabilities_to_inventory(
    capabilities: list[str], inventory_csv_content: str
) -> list[dict]:
    """
    Performs semantic search to map a list of business capabilities
    against an application inventory CSV.

    Args:
        capabilities: A list of capability strings (e.g., ["Identity Verification"]).
        inventory_csv_content: The full string content of the application CSV file.

    Returns:
        A list of dictionaries, each containing the capability, its best
        application match, and a confidence score.
    """
    logger.info("Starting capability mapping for %s capabilities.", len(capabilities))
    try:
        # --- 1. Process Application Inventory (The "Corpus") ---
        app_data = []
        f = io.StringIO(inventory_csv_content)
        reader = csv.DictReader(f)

        for row in reader:
            if "App_Name" not in row or "App_Description" not in row:
                continue

            # Create the text to be embedded (e.g., "Okta: Manages user identity and SSO")
            app_text = f"{row['App_Name']}: {row['App_Description']}"
            app_data.append({"name": row["App_Name"], "text": app_text})

        if not app_data:
            return [
                {
                    "error": "CSV processed, but no valid 'App_Name' or 'App_Description' rows found."
                }
            ]

        # --- 2. Get Embeddings ---
        app_names = [app["name"] for app in app_data]
        app_texts_for_embedding = [app["text"] for app in app_data]

        logger.info(
            "Generating embeddings for %s applications...", len(app_texts_for_embedding)
        )
        app_vectors = embedding_model.get_embeddings(app_texts_for_embedding)

        logger.info(
            "Generating embeddings for %s query capabilities...", len(capabilities)
        )
        cap_vectors = embedding_model.get_embeddings(capabilities)

        # Convert to NumPy arrays for fast calculation
        app_vectors_np = np.array([v.values for v in app_vectors])
        cap_vectors_np = np.array([v.values for v in cap_vectors])

        # --- 3. Perform Semantic Search (Cosine Similarity) ---
        # cdist returns "distance" (1 - similarity), so we subtract from 1
        similarities = 1 - cdist(cap_vectors_np, app_vectors_np, "cosine")

        # --- 4. Find Best Match for Each Capability ---
        results = []
        for i, capability in enumerate(capabilities):
            best_match_index = np.argmax(similarities[i])
            confidence = similarities[i][best_match_index]
            mapped_app = app_names[best_match_index]

            results.append(
                {
                    "capability": capability,
                    "mapped_app": mapped_app,
                    "confidence_score": round(float(confidence), 3),
                }
            )

        logger.info("Capability mapping complete.")
        return results

    except Exception as e:
        logger.error("Error during capability mapping: %s", e, exc_info=True)
        return [{"error": f"An exception occurred: {e}"}]


# --- Tool 2: Report Generation (Scenario 4) ---


def generate_capability_report_csv(report_data: list[dict], client_name: str) -> str:
    """
    Creates a CSV report from the full analysis data, uploads it to GCS,
    and returns a public URL.

    Args:
        report_data: A list of dictionaries. Each dict must contain keys:
                     'capability', 'source_snippet', 'mapped_app',
                     'confidence_score', 'criticality'.
        client_name: The client's name for the filename.

    Returns:
        A string containing the public URL of the generated CSV file or an error message.
    """
    bucket_name = os.getenv("GCS_BUCKET_NAME")
    if not bucket_name:
        return "Error: GCS_BUCKET_NAME is not configured."

    logger.info(
        "Generating CSV report for %s with %s items.", client_name, len(report_data)
    )
    try:
        filename = f"CapabilityReports/Capability-Analysis-{client_name}-{datetime.date.today()}.csv"

        with tempfile.NamedTemporaryFile(
            mode="w+", delete=False, suffix=".csv", newline="", encoding="utf-8"
        ) as tmp:
            # Define headers based on Scenario 4
            headers = [
                "Extracted Business Capability",
                "Source Text Snippet",
                "Mapped Application",
                "Confidence Score",
                "Criticality Level",
            ]
            writer = csv.DictWriter(tmp, fieldnames=headers)
            writer.writeheader()

            for item in report_data:
                # Map internal keys to friendly CSV headers
                writer.writerow(
                    {
                        "Extracted Business Capability": item.get("capability"),
                        "Source Text Snippet": item.get("source_snippet"),
                        "Mapped Application": item.get("mapped_app"),
                        "Confidence Score": item.get("confidence_score"),
                        "Criticality Level": item.get("criticality"),
                    }
                )

            tmp_path = tmp.name

        # Upload to GCS (reusing logic from your tools.py)
        storage_client = _get_gcs_client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(filename)
        blob.upload_from_filename(tmp_path, content_type="text/csv")

        os.remove(tmp_path)

        public_url = f"https://storage.googleapis.com/{bucket_name}/{filename}"

        logger.info("Uploaded CSV report to %s", public_url)
        return f"Successfully created the capability report. It is publicly accessible at: {public_url}"

    except Exception as e:
        logger.error("Error creating or uploading CSV report: %s", e, exc_info=True)
        return f"Error: Could not create or upload the report. Error: {e}"


# --- Tool Registration ---
map_capabilities_to_inventory_tool = FunctionTool(func=map_capabilities_to_inventory)
generate_capability_report_csv_tool = FunctionTool(func=generate_capability_report_csv)
