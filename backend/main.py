from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio
from models.pydantic_models import ChatRequest, ChatResponse

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

@app.get("/")
async def root():
    return {"status": "healthy", "message": "GitHub Repository Analysis API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/api/chat", response_model=ChatResponse)
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
            #model_kwargs={'temperature': 0.1},  # Lower temperature for more factual responses
            mcp_servers=[mcp_server]
        )
        
        async with chat_agent.run_mcp_servers():
            result = await chat_agent.run(
                f"""You are analyzing the GitHub repository {request.repository}.
                IMPORTANT: Only provide information that you can verify exists in the repository.
                If you cannot verify something, explicitly say so.
                Do not make assumptions or hallucinate details that aren't present.
                If you're unsure about something, say "I cannot verify this information in the repository."
                
                Question: {request.question}
                
                Provide a clear and factual response based only on verifiable repository content."""
            )
            
            # Extract the response content
            if isinstance(result, str):
                response_text = result
            else:
                # Try to get content from the response object
                if hasattr(result, '_all_messages'):
                    messages = result._all_messages
                    if len(messages) > 0:
                        last_message = messages[-1]
                        if hasattr(last_message, 'parts') and len(last_message.parts) > 0:
                            last_part = last_message.parts[-1]
                            if hasattr(last_part, 'content'):
                                response_text = last_part.content
                                return ChatResponse(response=response_text)
                
                # If direct access fails, try to get the data attribute
                if hasattr(result, 'data'):
                    response_text = str(result.data)
                else:
                    # Last resort: try to extract content using regex
                    import re
                    result_str = str(result)
                    content_match = re.search(r"content=['\"]([^'\"]*)['\"]", result_str)
                    if content_match:
                        response_text = content_match.group(1)
                    else:
                        response_text = "I cannot verify the requested information in the repository."
            
            return ChatResponse(response=response_text)
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error in chat: {str(e)}"
        )
