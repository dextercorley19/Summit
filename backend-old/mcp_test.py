#!/usr/bin/env python3
import os
import asyncio
from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio

# Load environment variables
load_dotenv()

# Get GitHub token from environment
github_token = os.getenv("GITHUB_TOKEN")
if not github_token:
    raise ValueError("GITHUB_TOKEN environment variable not found. Please check your .env file.")

# The repository we want to query
repo_name = "bennysun1/alien_height_prediction"
repo_url = "https://github.com/bennysun1/alien_height_prediction"

# Set up the MCP server using Docker as shown in the example
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
        'GITHUB_PERSONAL_ACCESS_TOKEN': github_token
    }
)

# Create the agent with the MCP server
agent = Agent(model='openai:gpt-4.1', mcp_servers=[server])

async def test_github_mcp():
    """Test GitHub MCP functionality by listing files in a repository"""
    print(f"Testing GitHub MCP with repository: {repo_url}")
    
    # Create conversation history to provide more context
    conversation = """
    You are analyzing the GitHub repository bennysun1/alien_height_prediction.
    
    User: Do any of these files exist in the repository? Please check each one and respond with Yes or No for each: 
    1) Height-Heredity-One-Generations-Impact.pdf 
    2) avg_parent_child.ipynb 
    3) ben_imputer_fix.ipynb 
    4) ben_notebook3_2_best.ipynb 
    5) cleaned_code.ipynb 
    6) final_height_prediction.ipynb 
    7) heritarty analysis.ipynb 
    8) rebekah119.ipynb 
    9) rebekah_cleaned_code.ipynb
    
    Assistant: Here are my findings after checking the bennysun1/alien_height_prediction repository for each specified file:
    
    1) Height-Heredity-One-Generations-Impact.pdf — No  
    2) avg_parent_child.ipynb — Yes  
    3) ben_imputer_fix.ipynb — Yes  
    4) ben_notebook3_2_best.ipynb — Yes  
    5) cleaned_code.ipynb — Yes  
    6) final_height_prediction.ipynb — Yes  
    7) heritarty analysis.ipynb — No  
    8) rebekah119.ipynb — Yes  
    9) rebekah_cleaned_code.ipynb — Yes
    
    User: Please double-check the full repository and list EVERY single file that exists in it.
    """
    
    try:
        # Run the agent with the MCP server
        async with agent.run_mcp_servers():
            result = await agent.run(conversation)
            print(f"Repository files:\n{result}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    # Run the async function
    asyncio.run(test_github_mcp()) 