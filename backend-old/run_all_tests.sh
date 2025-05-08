#!/bin/bash

# Exit on error
set -e

# Check if GITHUB_TOKEN is provided
if [ -z "$GITHUB_TOKEN" ]; then
  echo "Error: GITHUB_TOKEN environment variable is required."
  echo "Please set it with: export GITHUB_TOKEN=your_github_token"
  exit 1
fi

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Running All Summit Agent Tests ====${NC}"

# Part 1: Basic API Tests
echo -e "\n${YELLOW}=== PART 1: Basic API Tests ====${NC}"
./test_api.sh

# Part 2: GitHub API Tests
echo -e "\n${YELLOW}=== PART 2: GitHub API Tests ====${NC}"
./test_github_api.sh

# Part 3: Chat API Tests
echo -e "\n${YELLOW}=== PART 3: Chat API Tests ====${NC}"
./test_chat_api.sh

# Part 4: Service Monitoring
echo -e "\n${YELLOW}=== PART 4: Service Monitoring ====${NC}"
./monitor_service.sh

echo -e "\n${GREEN}=== All tests completed! ====${NC}"
echo -e "${GREEN}Your Summit Agent backend is successfully deployed and functioning.${NC}"
echo -e "${BLUE}Service URL: https://gitsummit-backend-sb5gnt3soq-uc.a.run.app${NC}"
echo -e "${BLUE}API Documentation: https://gitsummit-backend-sb5gnt3soq-uc.a.run.app/docs${NC}" 