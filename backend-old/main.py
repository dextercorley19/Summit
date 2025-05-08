from fastapi import HTTPException, Header
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

# FastAPI app and CORS middleware removed from here.
# The routes (@app.get("/"), @app.get("/health")) are also removed.

# The chat function remains, but it is no longer an active FastAPI route in this file.
# It can be imported and used elsewhere if needed.
async def chat_mcp_docker(request: ChatRequest, github_token: str = Header(..., alias="GitHub-Token", description="GitHub Personal Access Token")):
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
                                return ChatResponse(response=response_text) # This return is specific to FastAPI, adjust if used as a service
                
                # If direct access fails, try to get the data attribute
                if hasattr(result, 'data'):
                    response_text = str(result.data)
                else:
                    # Last resort: try to extract content using regex
                    import re
                    result_str = str(result)
                    content_match = re.search(r"content=['\\\"]([^'\\\"]*)['\\\"]", result_str)
                    if content_match:
                        response_text = content_match.group(1)
                    else:
                        response_text = "I cannot verify the requested information in the repository."
            
            return ChatResponse(response=response_text) # This return is specific to FastAPI, adjust if used as a service
    except Exception as e:
        logger.error(f"Error in chat_mcp_docker: {str(e)}")
        # This raise is specific to FastAPI, adjust if used as a service
        raise HTTPException(
            status_code=500,
            detail=f"Error in chat_mcp_docker: {str(e)}"
        )
