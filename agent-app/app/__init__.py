"""The application package."""

from app.agent import root_agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.agents.callback_context import CallbackContext
from google.adk.artifacts import GcsArtifactService

# InMemorySessionService is simple, non-persistent storage for this tutorial.
# session_service = InMemorySessionService()

# # Define constants for identifying the interaction context
# APP_NAME = "cloud_service_advisor_agent"
# USER_ID = "user_1"
# SESSION_ID = "session_001" # Using a fixed ID for simplicity

# # Create the specific session where the conversation will happen
# session = session_service.create_session(
#     app_name=APP_NAME,
#     user_id=USER_ID,
#     session_id=SESSION_ID
# )

# # invocation_context = CallbackContext(
# #     invocation_id="unique-id-for-this-run",
# #     session=session,
# #     user_content=user_message,
# #     agent=my_root_agent, # The starting agent
# #     session_service=session_service,
# #     artifact_service=artifact_service,
# #     memory_service=memory_service,
# #     # ... other necessary fields ...
# # )

# gcs_bucket_name_py = "your-gcs-bucket-for-adk-artifacts" # Replace with your bucket name

# try:
#     gcs_service_py = GcsArtifactService(bucket_name=gcs_bucket_name_py)
#     print(f"Python GcsArtifactService initialized for bucket: {gcs_bucket_name_py}")
#     # Ensure your environment has credentials to access this bucket.
#     # e.g., via Application Default Credentials (ADC)

#     # Then pass it to the Runner
#     # runner = Runner(..., artifact_service=gcs_service_py)

# except Exception as e:
#     # Catch potential errors during GCS client initialization (e.g., auth issues)
#     print(f"Error initializing Python GcsArtifactService: {e}")
#     # Handle the error appropriately - maybe fall back to InMemory or raise

# runner = Runner(
#     agent=root_agent, # The agent we want to run
#     app_name=APP_NAME,   # Associates runs with our app
#     session_service=session_service, # Uses our session manager
#     artifact_service=gcs_bucket_name_py
# )

__all__ = ["root_agent"]
