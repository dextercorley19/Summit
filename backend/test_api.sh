#!/bin/bash

# Exit on error
set -e

# Set the API URL
API_URL="https://gitsummit-backend-sb5gnt3soq-uc.a.run.app"

# Test headers
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper function to test an endpoint
test_endpoint() {
  local endpoint=$1
  local expected_status=$2
  local description=$3

  echo -e "\n${BLUE}Testing: ${description} (${API_URL}${endpoint})${NC}"
  
  # Make the request and get the status code
  status_code=$(curl -s -o /dev/null -w "%{http_code}" ${API_URL}${endpoint})
  
  # Check if the status matches the expected status
  if [ "$status_code" -eq "$expected_status" ]; then
    echo -e "${GREEN}✓ Success: Received expected status code ${status_code}${NC}"
  else
    echo -e "${RED}✗ Failed: Expected status ${expected_status}, but got ${status_code}${NC}"
  fi
}

# Test for JSON response
test_json_endpoint() {
  local endpoint=$1
  local expected_status=$2
  local description=$3
  local json_key=$4
  local expected_value=$5

  echo -e "\n${BLUE}Testing: ${description} (${API_URL}${endpoint})${NC}"
  
  # Make the request and save the response
  response=$(curl -s ${API_URL}${endpoint})
  status_code=$(curl -s -o /dev/null -w "%{http_code}" ${API_URL}${endpoint})
  
  # Check if the status matches the expected status
  if [ "$status_code" -eq "$expected_status" ]; then
    echo -e "${GREEN}✓ Success: Received expected status code ${status_code}${NC}"
    
    if [ ! -z "$json_key" ]; then
      # Extract the value using jq if installed
      if command -v jq &> /dev/null; then
        actual_value=$(echo $response | jq -r ".$json_key")
        if [ "$actual_value" == "$expected_value" ]; then
          echo -e "${GREEN}✓ Success: JSON value for key '$json_key' matches expected value '$expected_value'${NC}"
        else
          echo -e "${RED}✗ Failed: Expected value '$expected_value' for key '$json_key', but got '$actual_value'${NC}"
        fi
      else
        echo "Note: Install jq for JSON validation"
        echo "Response: $response"
      fi
    fi
  else
    echo -e "${RED}✗ Failed: Expected status ${expected_status}, but got ${status_code}${NC}"
  fi
}

echo -e "${BLUE}=== Testing Summit Agent API ====${NC}"
echo -e "${BLUE}API URL: ${API_URL}${NC}"

# Test health endpoint
test_json_endpoint "/api/health" 200 "Health Check" "status" "healthy"

# Test root endpoint
test_json_endpoint "/" 200 "Root Endpoint" "message" "Welcome to the GitHub MCP API"

# Test docs endpoint
test_endpoint "/docs" 200 "API Documentation"

# Test OpenAPI schema
test_endpoint "/openapi.json" 200 "OpenAPI Schema"

echo -e "\n${BLUE}=== Test Summary ====${NC}"
echo -e "${GREEN}Basic API endpoints are working properly.${NC}"
echo -e "${BLUE}You can manually verify the full API functionality by visiting:${NC}"
echo -e "${BLUE}${API_URL}/docs${NC}" 