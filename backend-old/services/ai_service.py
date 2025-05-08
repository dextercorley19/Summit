import logging
import asyncio
import os
from typing import List, Dict, Optional, Any
from pydantic_ai import Agent

# Try to import MCP components, but provide a fallback if not available
try:
    from pydantic_ai.mcp import MCPServerStdio, MCPServerTarget  # Added MCPServerTarget
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    # Define dummy classes to avoid errors
    class MCPServerStdio:
        def __init__(self, *args, **kwargs):
            pass

    class MCPServerTarget:  # Added dummy MCPServerTarget
        def __init__(self, *args, **kwargs):
            pass

from services.github_service import GitHubService

logger = logging.getLogger(__name__)

# Check if we're running in GCP (environment variable can be set in deployment)
IS_GCP_ENVIRONMENT = os.getenv("IS_GCP_ENVIRONMENT", "false").lower() == "true"
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")  # New: URL for the remote MCP server

class AIService:
    def __init__(self):
        self.github_service = GitHubService()
        
    async def chat_with_repo(self, repository: str, question: str, github_token: str, messages: List[Dict[str, str]] = None) -> str:
        """
        Chat with a repository using the GitHub MCP server or a fallback.
        
        Args:
            repository: Full name of the repository (e.g., "owner/repo")
            question: The user's question
            github_token: The user's GitHub personal access token (will be used by GitHubService, not directly by remote MCP server call from here)
            messages: List of previous messages in the conversation
            
        Returns:
            The AI's response as a clean string
        """
        try:
            if IS_GCP_ENVIRONMENT or not MCP_SERVER_URL:  # If no MCP_SERVER_URL, fallback to non-MCP
                logger.info("Running in GCP environment, MCP explicitly disabled, or MCP_SERVER_URL not set. Using non-MCP handler.")
                return await self._handle_question_without_mcp(repository, question, github_token, messages)
            else:
                logger.info(f"MCP_SERVER_URL is set to {MCP_SERVER_URL}, attempting to use remote MCP handler.")
                return await self._handle_question_with_mcp(repository, question, github_token, messages)
        except Exception as e:
            logger.error(f"Error in AI service dispatch: {str(e)}")
            return f"I encountered an error while processing your question: {str(e)}"
            
    async def _handle_question_without_mcp(self, repo_name: str, question: str, github_token: str, messages: List[Dict[str, str]] = None) -> str:
        """Demo version for GCP that doesn't rely on Docker MCP"""
        try:
            repo_context = await self._prepare_repo_context(repo_name, github_token)
            prompt = self._prepare_prompt(repo_context, question, messages)
            agent = Agent(model='openai:gpt-4.1')
            result = await agent.run(prompt)
            return self._extract_response_from_result(result)
        except Exception as e:
            logger.error(f"Error in _handle_question_without_mcp: {str(e)}")
            return f"I encountered an error while processing your question: {str(e)}"
    
    async def _handle_question_with_mcp(self, repo_name: str, question: str, github_token: str, messages: List[Dict[str, str]] = None) -> str:
        """Full version with MCP (now remote)"""
        try:
            if not MCP_AVAILABLE or not MCP_SERVER_URL:  # Should have been caught above, but double check
                logger.warning("MCP components not available or MCP_SERVER_URL not set, falling back to non-MCP handler.")
                return await self._handle_question_without_mcp(repo_name, question, github_token, messages)
                
            # Set up the remote MCP server target
            # The GITHUB_PERSONAL_ACCESS_TOKEN is now configured on the remote MCP server itself.
            # The `github_token` parameter for this method is for the GitHubService calls made by _prepare_repo_context.
            server = self._setup_mcp_server() 
            
            agent = Agent(model='openai:gpt-4.1', mcp_servers=[server])
            repo_context = await self._prepare_repo_context(repo_name, github_token)
            prompt = self._prepare_prompt(repo_context, question, messages)
            
            # For MCPServerTarget, run_mcp_servers() might not be needed or might behave differently.
            # Assuming it's still good practice or required by pydantic-ai's Agent.
            async with agent.run_mcp_servers(): 
                result = await agent.run(prompt)
                
            return self._extract_response_from_result(result)
        except Exception as e:
            logger.error(f"Error in _handle_question_with_mcp: {str(e)}")
            return f"I encountered an error while processing your question: {str(e)}"
            
    def _setup_mcp_server(self) -> Any:  # Return type Any to accommodate MCPServerTarget or dummy
        """Set up the GitHub MCP server (now as a remote target)."""
        if not MCP_AVAILABLE or not MCP_SERVER_URL:
            logger.warning("MCP components not available or MCP_SERVER_URL not set. Cannot set up MCP server.")
            # Return a dummy or raise an error, though this path should ideally not be hit
            # if checks in chat_with_repo are effective.
            return None 
            
        logger.info(f"Configuring remote MCP server target: {MCP_SERVER_URL}")
        # Assuming MCPServerTarget takes the URL of the remote MCP server.
        # The GITHUB_PERSONAL_ACCESS_TOKEN is expected to be set as an environment variable
        # on the machine/container running the actual github-mcp-server, not here.
        return MCPServerTarget(url=MCP_SERVER_URL)
        
    async def _prepare_repo_context(self, repo_name: str, github_token: str) -> str:
        """Prepare context information about the repository"""
        try:
            # Get repository details
            repos = self.github_service.get_user_repositories(github_token)
            repo = next((r for r in repos if r.name == repo_name), None)
            
            if not repo:
                return f"Could not find repository {repo_name}."
            
            # Build context information
            context = f"""
            Repository Information:
            - Name: {repo.name}
            - Full Name: {repo.full_name}
            - Description: {repo.description or 'No description available'}
            - Default Branch: {repo.default_branch}
            - Branches: {', '.join(repo.branches)}
            - Last Active: {repo.last_active}
            """
            
            return context
        except Exception as e:
            logger.error(f"Error preparing repository context: {str(e)}")
            return "Error retrieving repository information."
            
    def _prepare_prompt(self, context: str, question: str, messages: List[Dict[str, str]] = None) -> str:
        """
        Prepare the complete prompt for the AI
        
        Args:
            context: Repository context information
            question: The current question
            messages: Previous conversation history
            
        Returns:
            The complete prompt
        """
        # Start with system instructions
        prompt = f"""You are an AI assistant specialized in analyzing GitHub repositories. 
Your task is to provide helpful information about the repository based on the user's questions.

{context}

"""
        
        # Add conversation history if available
        if messages and len(messages) > 0:
            prompt += "Previous conversation:\n"
            for msg in messages:
                role = "User" if msg["role"] == "user" else "Assistant"
                prompt += f"{role}: {msg['content']}\n"
            
            prompt += "\n"
        
        # Add the current question
        prompt += f"User's question: {question}\n\nAssistant: "
        
        return prompt

    def _extract_response_from_result(self, result: Any) -> str:
        """Utility to extract string response from various possible AI agent result formats."""
        if isinstance(result, str):
            return result
        if hasattr(result, 'output') and result.output:
            return str(result.output)
        if hasattr(result, 'content') and result.content:
            return str(result.content)
        if hasattr(result, 'response') and result.response:
            return str(result.response)
        
        # Fallback for more complex structures like those with _all_messages
        if hasattr(result, '_all_messages'):
            messages = result._all_messages
            if messages and len(messages) > 0:
                last_message = messages[-1]
                if hasattr(last_message, 'parts') and last_message.parts and len(last_message.parts) > 0:
                    last_part = last_message.parts[-1]
                    if hasattr(last_part, 'content') and last_part.content:
                        return str(last_part.content)
        
        logger.warning(f"Could not extract a simple string from AI result: {type(result)}. Converting to string.")
        return str(result)