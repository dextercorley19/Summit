#!/usr/bin/env python3
import os
import asyncio
from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio

# Load environment variables from .env file
load_dotenv()

# Get GitHub token from environment
token = os.getenv("GITHUB_TOKEN")
if not token:
    raise ValueError("GITHUB_TOKEN environment variable not found. Please check your .env file.")

# The repository we want to query
repo_name = "bennysun1/alien_height_prediction"

# Set up the MCP server
server = MCPServerStdio(
    command='docker',
    args=[
        'run',
        '-i',
        '--rm',
        '-e',
        'GITHUB_PERSONAL_ACCESS_TOKEN',
        'ghcr.io/github/github-mcp-server',
    ],
    env={
        'GITHUB_PERSONAL_ACCESS_TOKEN': token
    }
)

# Create the agent
agent = Agent(model='openai:gpt-4.1', mcp_servers=[server])

async def test_github_mcp():
    """Test GitHub MCP functionality by listing files in a repository"""
    print(f"Testing GitHub MCP with repository: {repo_name}")
    
    # Create the prompt to list all files in the repository
    prompt = f"""
    You are a GitHub repository analyzer. You need to list ALL files in the repository {repo_name}.
    
    IMPORTANT:
    1. Do NOT skip any files
    2. Include all files regardless of their type or size
    3. Display the complete file list with their paths
    4. Do NOT summarize or group files
    5. If there are many files, list ALL of them, not just a sample
    
    Format your response as a simple bullet point list of all files in the repository.
    """
    
    try:
        # Run the agent with the MCP server
        async with agent.run_mcp_servers():
            result = await agent.run(prompt)
            print(f"Repository files:\n{result}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_github_mcp()) 