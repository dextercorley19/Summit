#!/bin/bash

# Exit on error
set -e

# Configuration
PROJECT_ID="mlops-final-project-459021"  # Your GCP project ID
REGION="us-central1"                     # Change this to your preferred region
SERVICE_NAME="gitsummit-backend"         # Name of your Cloud Run service
DOMAIN="api.summit-agent.online"         # The domain for your API

# Verify domain ownership
echo "To map a domain to your Cloud Run service, you need to verify domain ownership in Google Cloud."
echo "Please make sure you've verified ownership of summit-agent.online through Google Search Console or Google Domains."
echo "For instructions, visit: https://cloud.google.com/run/docs/mapping-custom-domains#verify_ownership_of_domain"
read -p "Have you verified domain ownership? (y/n): " verified

if [[ $verified != "y" ]]; then
  echo "Please verify domain ownership before proceeding."
  exit 1
fi

# Map domain to Cloud Run service
echo "Mapping domain ${DOMAIN} to service ${SERVICE_NAME}..."
gcloud beta run domain-mappings create \
  --service=${SERVICE_NAME} \
  --domain=${DOMAIN} \
  --region=${REGION} \
  --platform=managed

# Get the DNS records to configure
echo -e "\n=== DNS Configuration Required ==="
echo "Please add the following DNS records to your domain's DNS settings:"
gcloud beta run domain-mappings describe \
  --domain=${DOMAIN} \
  --region=${REGION} \
  --platform=managed \
  --format="value(status.resourceRecords)"

echo -e "\nDomain mapping created successfully."
echo "Your API will be accessible at: https://${DOMAIN} once DNS propagates (may take up to 24 hours)." 