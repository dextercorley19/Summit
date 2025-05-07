import logging
import asyncio
import os
from typing import List, Dict, Optional, Any
from pydantic_ai import Agent

# Try to import MCP, but provide a fallback if not available
try:
    from pydantic_ai.mcp import MCPServerStdio
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    # Define a dummy class to avoid errors
    class MCPServerStdio:
        def __init__(self, *args, **kwargs):
            pass

from services.github_service import GitHubService

logger = logging.getLogger(__name__)

# Check if we're running in GCP (environment variable can be set in deployment)
IS_GCP_ENVIRONMENT = os.getenv("IS_GCP_ENVIRONMENT", "false").lower() == "true"

class AIService:
    def __init__(self, github_token: str):
        self.github_token = github_token
        self.github_service = GitHubService(github_token)
        
    async def chat_with_repo(self, repository: str, question: str, messages: List[Dict[str, str]] = None) -> str:
        """
        Chat with a repository using the GitHub MCP server
        
        Args:
            repository: Full name of the repository (e.g., "owner/repo")
            question: The user's question
            messages: List of previous messages in the conversation
            
        Returns:
            The AI's response as a clean string
        """
        try:
            # Use a standard Agent without MCP in GCP
            agent = Agent(model='openai:gpt-4.1')
            
            # Build conversation history
            conversation = f"""You are analyzing the GitHub repository {repository}.
                IMPORTANT INSTRUCTIONS:
                1. Analyze the repository's code files, documentation, and structure.
                2. Provide information that you can verify exists in the repository.
                3. When discussing code elements (functions, classes, variables), cite them if you can find them.
                4. If you cannot verify something, explicitly say "I cannot verify [specific detail] in the repository."
                5. Do not make assumptions or hallucinate details that aren't present.
                6. Focus on providing factual, code-based responses.
                
                """
            
            # Add conversation history if available
            if messages:
                conversation += "Previous conversation:\n"
                for msg in messages:
                    role = msg.get('role', 'user')  # Default to user if role not specified
                    content = msg.get('content', '')
                    conversation += f"{role.capitalize()}: {content}\n"
                conversation += "\n"
            
            # Add current question
            conversation += f"User: {question}\n\nAssistant: "
            
            # Run the agent with the complete conversation
            result = await agent.run(conversation)
            
            # Extract the actual response content
            if isinstance(result, str):
                return result
                
            # Try to get the response from various attributes
            if hasattr(result, '_all_messages'):
                messages = result._all_messages
                if len(messages) > 0:
                    last_message = messages[-1]
                    if hasattr(last_message, 'parts') and len(last_message.parts) > 0:
                        last_part = last_message.parts[-1]
                        if hasattr(last_part, 'content'):
                            return last_part.content
            
            # Fallback to other attributes
            if hasattr(result, 'data'):
                return str(result.data)
            elif hasattr(result, 'content'):
                return str(result.content)
            elif hasattr(result, 'response'):
                return str(result.response)
            else:
                # Last resort: convert to string but clean it up
                return str(result).strip()
        except Exception as e:
            logger.error(f"Error in AI service: {str(e)}")
            return f"I encountered an error while processing your question: {str(e)}"
            
    async def _handle_question_without_mcp(self, repo_name: str, question: str, messages: List[Dict[str, str]] = None) -> str:
        """Demo version for GCP that doesn't rely on Docker MCP"""
        try:
            # Get repository context
            repo_context = await self._prepare_repo_context(repo_name)
            
            # Prepare the prompt
            prompt = self._prepare_prompt(repo_context, question, messages)
            
            # Use a standard Agent without MCP
            agent = Agent(model='openai:gpt-4.1')
            result = await agent.run(prompt)
            
            # Handle different result formats
            if hasattr(result, 'output'):
                return result.output
            elif hasattr(result, 'content'):
                return result.content
            elif hasattr(result, 'response'):
                return result.response
            elif isinstance(result, str):
                return result
            else:
                # Last resort: convert to string
                return str(result)
        except Exception as e:
            logger.error(f"Error in _handle_question_without_mcp: {str(e)}")
            return f"I encountered an error while processing your question: {str(e)}"
    
    async def _handle_question_with_mcp(self, repo_name: str, question: str, messages: List[Dict[str, str]] = None) -> str:
        """Full version with MCP for local development"""
        try:
            # Check if MCP is available
            if not MCP_AVAILABLE:
                return await self._handle_question_without_mcp(repo_name, question, messages)
                
            # Set up the MCP server with Docker
            server = self._setup_mcp_server()
            
            # Initialize the agent
            agent = Agent(model='openai:gpt-4.1', mcp_servers=[server])
            
            # Prepare context about the repository
            repo_context = await self._prepare_repo_context(repo_name)
            
            # Prepare the complete prompt with context, history, and the current question
            prompt = self._prepare_prompt(repo_context, question, messages)
            
            # Run the agent
            async with agent.run_mcp_servers():
                result = await agent.run(prompt)
                
            # Handle different result formats
            if hasattr(result, 'output'):
                return result.output
            elif hasattr(result, 'content'):
                return result.content
            elif hasattr(result, 'response'):
                return result.response
            elif isinstance(result, str):
                return result
            else:
                # Last resort: convert to string
                return str(result)
        except Exception as e:
            logger.error(f"Error in _handle_question_with_mcp: {str(e)}")
            return f"I encountered an error while processing your question: {str(e)}"
            
    def _setup_mcp_server(self) -> MCPServerStdio:
        """Set up the GitHub MCP server"""
        if not MCP_AVAILABLE:
            logger.warning("MCP is not available, returning dummy server.")
            return MCPServerStdio()
            
        return MCPServerStdio(
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
                'GITHUB_PERSONAL_ACCESS_TOKEN': self.github_token
            }
        )
        
    async def _prepare_repo_context(self, repo_name: str) -> str:
        """Prepare context information about the repository"""
        try:
            # Get repository details
            repos = self.github_service.get_user_repositories()
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