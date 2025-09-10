# export GOOGLE_CLOUD_PROJECT=agents-stg
# export GOOGLE_CLOUD_LOCATION=us-central1
# export GOOGLE_GENAI_USE_VERTEXAI=True

# gcloud run deploy agent-service-recommender \
# --source . \
# --memory "4Gi" \
# --project $GOOGLE_CLOUD_PROJECT \
# --region "us-central1" \
# --labels "created-by=jarvis" \
# --allow-unauthenticated \
# --port 8080 \
# --set-build-env-vars=GOOGLE_ENTRYPOINT="uv run uvicorn app.server:app --host 0.0.0.0 --port 8080"

gcloud beta run deploy cloud-service-recommender \
		--source . \
		--memory "4Gi" \
		--project "agents-stg" \
		--region "us-central1" \
		--labels "created-by=jarvis" \
		--allow-unauthenticated \
		--port 8080

gcloud beta run deploy cloud-service-recommender \
		--source . \
		--memory "4Gi" \
		--project "sample-project-468209" \
		--region "us-central1" \
		--labels "created-by=jarvis" \
		--allow-unauthenticated \
		--port 8080
