from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import asyncio
from typing import List, Dict, Any
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio
import json
import logging
from dotenv import load_dotenv
from services.github_service import GitHubService

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RepositoryResponse(BaseModel):
    repositories: List[Dict[str, str]]

class ChatRequest(BaseModel):
    repository: str
    question: str

class AnalyzeRequest(BaseModel):
    repository: str

# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware with more permissive settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://localhost:3000", "https://summit-agent.online"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Retrieve the GitHub token from environment variables
token = os.getenv('GITHUB_PERSONAL_ACCESS_TOKEN') or os.getenv('GITHUB_TOKEN')
if not token:
    # For demo purposes, continue even without a token
    print("WARNING: GITHUB_PERSONAL_ACCESS_TOKEN is not set in environment variables.")
    token = "dummy_token_for_initialization"

# Set up the MCP server only if the module is available
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

# Create agent instance
agent = Agent(
    model='openai:gpt-4.1',
    model_kwargs={'temperature': 0.1},
    mcp_servers=[server]
)

@app.get("/")
async def root():
    return {"status": "healthy", "message": "GitHub Repository Analysis API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/repositories", response_model=RepositoryResponse)
async def list_repositories(github_token: str = Header(..., alias="GitHub-Token", description="GitHub Personal Access Token")):
    try:
        logger.info("Fetching repositories using GitHub API")
        github_service = GitHubService(github_token)
        
        # Validate the token
        if not github_service.validate_token():
            raise HTTPException(status_code=401, detail="Invalid GitHub token")
        
        # Get repositories
        repos = github_service.get_user_repositories()
        
        # Convert to response format
        repositories = []
        for repo in repos:
            repositories.append({
                "full_name": repo.full_name,
                "owner": repo.full_name.split('/')[0],
                "name": repo.name
            })
            
        logger.info(f"Found {len(repositories)} repositories")
        return {"repositories": repositories}
    except Exception as e:
        logger.error(f"Error listing repositories: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error listing repositories: {str(e)}"
        )

@app.post("/api/analyze")
async def analyze_repository(request: AnalyzeRequest, github_token: str = Header(..., alias="GitHub-Token", description="GitHub Personal Access Token")):
    try:
        logger.info(f"Analyzing repository: {request.repository}")
        
        # Set up MCP server with the provided token
        mcp_server = MCPServerStdio(
            command='docker',
            args=[
                'run',
                '-i',
                '--rm',
                '-e',
                'GITHUB_PERSONAL_ACCESS_TOKEN',
                'ghcr.io/github/github-mcp-server',
            ],
            env={'GITHUB_PERSONAL_ACCESS_TOKEN': github_token}
        )
        
        # Create a new agent instance with the user's token
        analyze_agent = Agent(
            model='openai:gpt-4.1',
            model_kwargs={'temperature': 0.1},
            mcp_servers=[mcp_server]
        )
        
        async with analyze_agent.run_mcp_servers():
            result = await analyze_agent.run(
                f"""Analyze the repository {request.repository}.
                Provide:
                1. Overall code quality score (0-10)
                2. Key insights about the codebase
                3. Areas for improvement
                4. Recent changes and their impact
                
                Format as JSON with these fields:
                {{
                    "overall_score": number,
                    "summary": string,
                    "file_analyses": object
                }}"""
            )
        
        # Ensure the response is valid JSON
        try:
            return json.loads(result.output)
        except json.JSONDecodeError:
            logger.warning("Failed to parse analysis result as JSON")
            return {"error": "Invalid JSON response", "raw_response": result.output}
            
    except Exception as e:
        logger.error(f"Error analyzing repository: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing repository: {str(e)}"
        )

@app.post("/api/chat")
async def chat(request: ChatRequest, github_token: str = Header(..., alias="GitHub-Token", description="GitHub Personal Access Token")):
    try:
        logger.info(f"Chat request for repository: {request.repository}")
        
        # Set up MCP server with the provided token
        mcp_server = MCPServerStdio(
            command='docker',
            args=[
                'run',
                '-i',
                '--rm',
                '-e',
                'GITHUB_PERSONAL_ACCESS_TOKEN',
                'ghcr.io/github/github-mcp-server',
            ],
            env={'GITHUB_PERSONAL_ACCESS_TOKEN': github_token}
        )
        
        # Create a new agent instance with the user's token
        chat_agent = Agent(
            model='openai:gpt-4.1',
            model_kwargs={'temperature': 0.1},
            mcp_servers=[mcp_server]
        )
        
        async with chat_agent.run_mcp_servers():
            result = await chat_agent.run(
                f"""Question about repository {request.repository}:
                {request.question}
                
                Provide a clear and concise response."""
            )
        return {"response": result.output}
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error in chat: {str(e)}"
        )
