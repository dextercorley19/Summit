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

# Test headers
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Testing GitHub Integration ====${NC}"
echo -e "${BLUE}API URL: ${API_URL}${NC}"

# Test get repositories endpoint
echo -e "\n${BLUE}Testing: Get User Repositories${NC}"
response=$(curl -s -H "GitHub-Token: $GITHUB_TOKEN" "${API_URL}/api/repositories")
status_code=$(curl -s -o /dev/null -w "%{http_code}" -H "GitHub-Token: $GITHUB_TOKEN" "${API_URL}/api/repositories")

if [ "$status_code" -eq 200 ]; then
  echo -e "${GREEN}✓ Success: Received repositories list (Status: ${status_code})${NC}"
  
  # Extract the first repository name using jq (if installed)
  if command -v jq &> /dev/null; then
    repo_count=$(echo "$response" | jq length)
    echo -e "${GREEN}  Found ${repo_count} repositories${NC}"
    
    if [ "$repo_count" -gt 0 ]; then
      first_repo=$(echo "$response" | jq -r '.[0].name')
      echo -e "${GREEN}  First repository: ${first_repo}${NC}"
      
      # Test branches endpoint
      echo -e "\n${BLUE}Testing: Get Repository Branches${NC}"
      branches_response=$(curl -s -H "GitHub-Token: $GITHUB_TOKEN" "${API_URL}/api/repositories/${first_repo}/branches")
      branches_status=$(curl -s -o /dev/null -w "%{http_code}" -H "GitHub-Token: $GITHUB_TOKEN" "${API_URL}/api/repositories/${first_repo}/branches")
      
      if [ "$branches_status" -eq 200 ]; then
        echo -e "${GREEN}✓ Success: Received branches (Status: ${branches_status})${NC}"
        branch_count=$(echo "$branches_response" | jq '.branches | length')
        echo -e "${GREEN}  Found ${branch_count} branches${NC}"
        
        # Test contents endpoint
        echo -e "\n${BLUE}Testing: Get Repository Contents${NC}"
        contents_response=$(curl -s -H "GitHub-Token: $GITHUB_TOKEN" "${API_URL}/api/repositories/${first_repo}/contents")
        contents_status=$(curl -s -o /dev/null -w "%{http_code}" -H "GitHub-Token: $GITHUB_TOKEN" "${API_URL}/api/repositories/${first_repo}/contents")
        
        if [ "$contents_status" -eq 200 ]; then
          echo -e "${GREEN}✓ Success: Received repository contents (Status: ${contents_status})${NC}"
          content_count=$(echo "$contents_response" | jq '.contents | length')
          echo -e "${GREEN}  Found ${content_count} items in the repository root${NC}"
        else
          echo -e "${RED}✗ Failed: Could not get repository contents (Status: ${contents_status})${NC}"
        fi
      else
        echo -e "${RED}✗ Failed: Could not get branches (Status: ${branches_status})${NC}"
      fi
    else
      echo -e "${RED}  No repositories found to test with${NC}"
    fi
  else
    echo -e "${RED}jq not installed. Install it for better output parsing${NC}"
    echo -e "Response preview: ${response:0:100}..."
  fi
else
  echo -e "${RED}✗ Failed: Could not get repositories (Status: ${status_code})${NC}"
  echo -e "Response: $response"
fi

echo -e "\n${BLUE}=== Test Summary ====${NC}"
if [ "$status_code" -eq 200 ]; then
  echo -e "${GREEN}GitHub API integration is working properly.${NC}"
  echo -e "${BLUE}You can test more functionality through the API docs:${NC}"
  echo -e "${BLUE}${API_URL}/docs${NC}"
else
  echo -e "${RED}GitHub API integration has issues.${NC}"
  echo -e "${RED}Check your GitHub token and try again.${NC}"
fi 