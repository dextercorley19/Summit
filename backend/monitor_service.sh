#!/bin/bash

# Exit on error
set -e

# Configuration
PROJECT_ID="mlops-final-project-459021"  # Your GCP project ID
REGION="us-central1"                     # Change this to your preferred region
SERVICE_NAME="gitsummit-backend"         # Name of your Cloud Run service

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Monitoring GCP Cloud Run Service ====${NC}"
echo -e "${BLUE}Service: ${SERVICE_NAME}${NC}"
echo -e "${BLUE}Project: ${PROJECT_ID}${NC}"
echo -e "${BLUE}Region: ${REGION}${NC}"

# Check service status
echo -e "\n${BLUE}Checking service status...${NC}"
gcloud run services describe ${SERVICE_NAME} \
  --platform managed \
  --region ${REGION} \
  --format="value(status.conditions)" | sed 's/;//g'

# Get service URL
echo -e "\n${BLUE}Service URL:${NC}"
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
  --platform managed \
  --region ${REGION} \
  --format="value(status.url)")
echo -e "${GREEN}${SERVICE_URL}${NC}"

# Check service traffic allocation
echo -e "\n${BLUE}Traffic allocation:${NC}"
gcloud run services describe ${SERVICE_NAME} \
  --platform managed \
  --region ${REGION} \
  --format="value(status.traffic)" | sed 's/;//g'

# Check resource allocation
echo -e "\n${BLUE}Resource allocation:${NC}"
gcloud run services describe ${SERVICE_NAME} \
  --platform managed \
  --region ${REGION} \
  --format="value(spec.template.spec.containers[0].resources)" | sed 's/;//g'

# View recent logs
echo -e "\n${BLUE}Recent logs:${NC}"
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=${SERVICE_NAME}" \
  --project=${PROJECT_ID} \
  --limit=5 \
  --format="table(timestamp, textPayload, jsonPayload.message)"

# Get service revisions
echo -e "\n${BLUE}Service revisions:${NC}"
gcloud run revisions list \
  --platform managed \
  --region ${REGION} \
  --service ${SERVICE_NAME} \
  --format="table(metadata.name, status.conditions[5].type, status.conditions[5].status, resource.limits)"

# Monitor health
echo -e "\n${BLUE}Checking service health...${NC}"
curl -s "${SERVICE_URL}/api/health" | jq || echo -e "${RED}Health check failed${NC}"

echo -e "\n${BLUE}=== Monitoring Complete ====${NC}"
echo -e "${YELLOW}To view metrics and logs in the GCP Console, visit:${NC}"
echo -e "${YELLOW}https://console.cloud.google.com/run/detail/${REGION}/${SERVICE_NAME}/metrics?project=${PROJECT_ID}${NC}" 