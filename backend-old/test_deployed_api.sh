#!/bin/bash

# Load variables from .env
source .env 2>/dev/null || echo "No .env file found, using command line arguments"

# Use environment variables or command-line args
GITHUB_TOKEN=${1:-$GITHUB_TOKEN}
API_URL=${2:-"https://gitsummit-backend-unique-id.a.run.app"}  # Replace with your actual URL after deployment

if [ -z "$GITHUB_TOKEN" ]; then
    echo "Error: GitHub token is required"
    echo "Usage: $0 [github_token] [api_url]"
    exit 1
fi

echo "Testing deployed API at $API_URL"

# Test health endpoint
echo -e "\n1. Testing health endpoint..."
curl -s "$API_URL/api/health" | jq

# Test authentication endpoint
echo -e "\n2. Testing authentication endpoint..."
curl -s -X POST "$API_URL/api/auth/github" \
  -H "Content-Type: application/json" \
  -d "{\"github_token\": \"$GITHUB_TOKEN\"}" | jq

# Test repository listing
echo -e "\n3. Testing repository listing..."
curl -s -X GET "$API_URL/api/repositories" \
  -H "github-token: $GITHUB_TOKEN" | jq

# Choose a repository from the list for further testing
echo -e "\n4. Enter a repository name to test (or press enter to use default 'gitsummit_frontend'):"
read REPO_NAME
REPO_NAME=${REPO_NAME:-"gitsummit_frontend"}

# Test chat functionality
echo -e "\n5. Testing chat functionality with repository: $REPO_NAME"
RESPONSE=$(curl -s -X POST "$API_URL/api/chat" \
  -H "Content-Type: application/json" \
  -d "{\"github_token\": \"$GITHUB_TOKEN\", \"repo_name\": \"$REPO_NAME\", \"question\": \"What is this repository about?\"}")

echo "$RESPONSE" | jq

# Extract conversation ID for next test
CONVERSATION_ID=$(echo "$RESPONSE" | jq -r '.conversation_id')

# Test conversation history
echo -e "\n6. Testing conversation history endpoint..."
curl -s -X GET "$API_URL/api/chat/history/$REPO_NAME" | jq

# Test specific conversation
echo -e "\n7. Testing specific conversation endpoint..."
curl -s -X GET "$API_URL/api/chat/$CONVERSATION_ID" | jq

echo -e "\nAll tests completed!" 