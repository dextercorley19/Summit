#!/bin/bash

# Exit on error
set -e

# Check if GITHUB_TOKEN is provided
if [ -z "$GITHUB_TOKEN" ]; then
  echo "Error: GITHUB_TOKEN environment variable is required."
  echo "Please set it with: export GITHUB_TOKEN=your_github_token"
  exit 1
fi

# Set the API URL
API_URL="https://gitsummit-backend-sb5gnt3soq-uc.a.run.app"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Testing Chat API with Pydantic AI ====${NC}"
echo -e "${BLUE}API URL: ${API_URL}${NC}"

# First get a list of repositories
echo -e "\n${BLUE}Fetching user repositories...${NC}"
response=$(curl -s -H "GitHub-Token: $GITHUB_TOKEN" "${API_URL}/api/repositories")
status_code=$(curl -s -o /dev/null -w "%{http_code}" -H "GitHub-Token: $GITHUB_TOKEN" "${API_URL}/api/repositories")

if [ "$status_code" -eq 200 ]; then
  # If jq is installed, use it to get the first repository
  if command -v jq &> /dev/null; then
    repo_count=$(echo "$response" | jq length)
    
    if [ "$repo_count" -gt 0 ]; then
      repo_name=$(echo "$response" | jq -r '.[0].name')
      echo -e "${GREEN}Using repository: ${repo_name}${NC}"
      
      # Create a simple chat request
      echo -e "\n${BLUE}Testing Chat API with a simple question...${NC}"
      # This might take some time as it interacts with the AI
      echo -e "${BLUE}(This may take a minute - the AI is analyzing the repository)${NC}"

      chat_payload='{
        "repo_name": "'$repo_name'",
        "github_token": "'$GITHUB_TOKEN'",
        "question": "What is this repository about? Give a short summary.",
        "messages": []
      }'
      
      # Make the chat request
      chat_response=$(curl -s -X POST -H "Content-Type: application/json" -d "$chat_payload" "${API_URL}/api/chat")
      chat_status=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H "Content-Type: application/json" -d "$chat_payload" "${API_URL}/api/chat")
      
      # Check the status
      if [ "$chat_status" -eq 200 ]; then
        echo -e "${GREEN}✓ Chat API responded successfully (Status: ${chat_status})${NC}"
        
        # Extract conversation ID and response using jq
        if command -v jq &> /dev/null; then
          conv_id=$(echo "$chat_response" | jq -r '.conversation_id')
          ai_response=$(echo "$chat_response" | jq -r '.response')
          
          echo -e "${GREEN}Conversation ID: ${conv_id}${NC}"
          echo -e "${GREEN}AI Response:${NC}"
          echo -e "${GREEN}${ai_response}${NC}"
          
          # Check conversation history
          echo -e "\n${BLUE}Testing conversation history...${NC}"
          history_response=$(curl -s "${API_URL}/api/chat/history/${repo_name}")
          history_status=$(curl -s -o /dev/null -w "%{http_code}" "${API_URL}/api/chat/history/${repo_name}")
          
          if [ "$history_status" -eq 200 ]; then
            echo -e "${GREEN}✓ Successfully retrieved conversation history (Status: ${history_status})${NC}"
            history_count=$(echo "$history_response" | jq 'length')
            echo -e "${GREEN}Found ${history_count} conversations for repository ${repo_name}${NC}"
            
            # Check specific conversation
            echo -e "\n${BLUE}Testing specific conversation retrieval...${NC}"
            conv_response=$(curl -s "${API_URL}/api/chat/${conv_id}")
            conv_status=$(curl -s -o /dev/null -w "%{http_code}" "${API_URL}/api/chat/${conv_id}")
            
            if [ "$conv_status" -eq 200 ]; then
              echo -e "${GREEN}✓ Successfully retrieved conversation details (Status: ${conv_status})${NC}"
              msg_count=$(echo "$conv_response" | jq '.messages | length')
              echo -e "${GREEN}Conversation has ${msg_count} messages${NC}"
            else
              echo -e "${RED}✗ Failed to retrieve conversation details (Status: ${conv_status})${NC}"
              echo -e "Response: $conv_response"
            fi
          else
            echo -e "${RED}✗ Failed to retrieve conversation history (Status: ${history_status})${NC}"
            echo -e "Response: $history_response"
          fi
        else
          echo -e "${RED}jq not installed. Raw response:${NC}"
          echo "$chat_response"
        fi
      else
        echo -e "${RED}✗ Chat API request failed (Status: ${chat_status})${NC}"
        echo -e "Response: $chat_response"
      fi
    else
      echo -e "${RED}No repositories found to test with${NC}"
    fi
  else
    echo -e "${RED}jq not installed. Cannot parse repository list.${NC}"
  fi
else
  echo -e "${RED}✗ Failed to get repositories (Status: ${status_code})${NC}"
  echo -e "Response: $response"
fi

echo -e "\n${BLUE}=== Test Summary ====${NC}"
if [ "$status_code" -eq 200 ] && [ "$chat_status" -eq 200 ]; then
  echo -e "${GREEN}Chat API with Pydantic AI is working properly.${NC}"
  echo -e "${BLUE}You can further test the API through:${NC}"
  echo -e "${BLUE}${API_URL}/docs${NC}"
else
  echo -e "${RED}Chat API integration has issues.${NC}"
  echo -e "${RED}Check the API logs in Google Cloud Console for more details.${NC}"
fi 