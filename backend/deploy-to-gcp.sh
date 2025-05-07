#!/bin/bash

# Exit on error
set -e

# Check for required environment variables
if [ -z "$GITHUB_TOKEN" ]; then
  echo "Error: GITHUB_TOKEN environment variable is required."
  echo "Please set it with: export GITHUB_TOKEN=your_github_token"
  exit 1
fi

# Configuration
PROJECT_ID="mlops-final-project-459021"  # Your GCP project ID
REGION="us-central1"                     # Change this to your preferred region
SERVICE_NAME="gitsummit-backend"         # Name of your Cloud Run service
REPOSITORY="gitsummit"                   # Name for your Artifact Registry repository
IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${SERVICE_NAME}:latest"

# Create Artifact Registry repository if it doesn't exist
echo "Setting up Artifact Registry repository..."
gcloud artifacts repositories create ${REPOSITORY} \
    --repository-format=docker \
    --location=${REGION} \
    --description="Docker repository for GitSummit" \
    --quiet || true  # Suppress error if already exists

# Configure Docker for Artifact Registry
echo "Configuring Docker for Artifact Registry..."
gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet

# Build the Docker image
echo "Building Docker image with platform linux/amd64..."
docker buildx build --platform linux/amd64 -t ${IMAGE_NAME} . --push

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --memory 1Gi \
  --set-env-vars="IS_GCP_ENVIRONMENT=true,GITHUB_TOKEN=${GITHUB_TOKEN}"

echo "Deployment complete!"
echo "Your API is available at: $(gcloud run services describe ${SERVICE_NAME} --platform managed --region ${REGION} --format 'value(status.url)')" 