from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio
import os
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "www.summit-agent.online"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    question: str
    github_token: str

@app.post("/api/chat")
async def chat_with_repo(request: ChatRequest):
    try:
        if not request.github_token:
            raise HTTPException(status_code=400, detail="GitHub token is required")

        # Set up the MCP server with Docker
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
                'GITHUB_PERSONAL_ACCESS_TOKEN': request.github_token
            }
        )

        # Initialize the agent
        agent = Agent(model='openai:gpt-4.1', mcp_servers=[server])

        # Create a new event loop for this request
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def process_request():
            async with agent.run_mcp_servers():
                result = await agent.run(request.question)
                return result.output

        # Run the request in the new loop
        response = await process_request()
        
        return {"response": response}

    except Exception as e:
        print(f"Detailed error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)