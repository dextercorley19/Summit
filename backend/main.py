from fastapi import FastAPI
import os
import asyncio
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
from pydantic import BaseModel

from backend.settings.constants import LOCAL_FRONTEND_URL

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

class RepoRequest(BaseModel):
    user_name: str
    repo_name: str

class CollabRequest(BaseModel):
    repo_name: str

class ChatRequest(BaseModel):
    github_token: str
    question: str
    messages: List[Dict[str, str]]

app = FastAPI()
agent = Agent(model='openai:gpt-4.1-mini', mcp_servers=[server])

# Allow cross-origin resource sharing between local api deployment and frontend deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=[LOCAL_FRONTEND_URL, "www.summit-agent.online"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return "Welcome to the Git-SummitAgent Alpha API! Hear over to the /docs for a list of our **agentic** endpoints."

@app.get("/count-repositories")
async def count_repositories():
    async with agent.run_mcp_servers():
        # Run a sample query
        result = await agent.run('Count how many repositories I have.')
    
    return result.output

@app.get("/get-commit-history")
async def get_commit_history(request: RepoRequest):
    async with agent.run_mcp_servers():
        # Run a sample query
        result = await agent.run(f'Fetch the commit history for user {request.user_name} in the {request.repo_name} repo.')
    
    return result.output

@app.get("/get-contributors")
async def get_collaborators(request: CollabRequest):
    async with agent.run_mcp_servers():
        # Run a sample query
        result = await agent.run(f'List the contributors in the {request.repo_name} repo.')
    
    return result.output

@app.post("/chat")
async def process_query(request: ChatRequest):
    # Concatenate previous messages for context
    conversation = ""
    for msg in request.messages:
        role = "User" if msg["type"] == "user" else ("Assistant" if msg["type"] == "bot" else "Error")
        conversation += f"{role}: {msg['content']}\n"
    conversation += f"User: {request.question}\n"

    async with agent.run_mcp_servers():
        result = await agent.run(conversation)
    
    return {"response": result.output}
