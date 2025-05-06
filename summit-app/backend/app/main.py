from fastapi import FastAPI, HTTPException, Request
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

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RepositoryResponse(BaseModel):
    repositories: List[Dict[str, str]]

class ChatRequest(BaseModel):
    question: str
    repository: str

class AnalyzeRequest(BaseModel):
    repository: str

# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware with more permissive settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Retrieve the GitHub token from environment variables
token = os.getenv('GITHUB_PERSONAL_ACCESS_TOKEN')
if not token:
    raise ValueError("GITHUB_PERSONAL_ACCESS_TOKEN is not set in environment variables.")

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
async def list_repositories(request: Request):
    try:
        logger.info("Fetching repositories")
        async with agent.run_mcp_servers():
            result = await agent.run("""List all repositories I have access to.
            Format the output as a JSON array of objects with 'owner' and 'name' fields.
            Only include repositories I can read.
            Sort by last modified date (newest first).
            Limit to 10 repositories.
            Example format:
            [
                {"owner": "username", "name": "repo-name"},
                {"owner": "org-name", "name": "another-repo"}
            ]
            Do not include any other text in the response, just the JSON array.""")
            
            try:
                # Clean the result string - remove any non-JSON text
                json_str = result.output.strip()
                # Find the first '[' and last ']' to extract just the JSON array
                start = json_str.find('[')
                end = json_str.rfind(']') + 1
                if start != -1 and end != -1:
                    json_str = json_str[start:end]
                    data = json.loads(json_str)
                    if isinstance(data, list):
                        repositories = []
                        for repo in data:
                            if isinstance(repo, dict) and 'owner' in repo and 'name' in repo:
                                repositories.append({
                                    "full_name": f"{repo['owner']}/{repo['name']}",
                                    "owner": repo['owner'],
                                    "name": repo['name']
                                })
                        logger.info(f"Found {len(repositories)} repositories")
                        return {"repositories": repositories}
                
                logger.warning("Invalid JSON structure in response")
                return {"repositories": []}
                
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON response: {e}")
                return {"repositories": []}
                
    except Exception as e:
        logger.error(f"Error listing repositories: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error listing repositories: {str(e)}"
        )

@app.post("/api/analyze")
async def analyze_repository(request: AnalyzeRequest):
    try:
        logger.info(f"Analyzing repository: {request.repository}")
        async with agent.run_mcp_servers():
            result = await agent.run(
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
async def chat(request: ChatRequest):
    try:
        logger.info(f"Chat request for repository: {request.repository}")
        async with agent.run_mcp_servers():
            result = await agent.run(
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
