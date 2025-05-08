import logging
import asyncio
import os
from typing import List, Dict, Any
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio
from services.github_service import GitHubService

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.github_service = GitHubService()
        # Initialize MCPServerStdio similar to backend/main.py
        # The GITHUB_PERSONAL_ACCESS_TOKEN will be set dynamically per request via self.mcp_server.env
        self.mcp_server = MCPServerStdio(
            command='docker',
            args=[
                'run',
                '-i',  # For stdin
                '--rm', # Remove container after exit
                '-e',  # Pass environment variable
                'GITHUB_PERSONAL_ACCESS_TOKEN', # Variable name, value set per request
                # Consider making the image name a constant or env variable
                'ghcr.io/github/github-mcp-server', 
            ],
        )
        # Initialize Agent with the MCP server
        # Ensure the model name is appropriate, e.g., 'openai:gpt-4.1-mini' or 'openai:gpt-4.1'
        self.agent = Agent(model='openai:gpt-4.1-mini', mcp_servers=[self.mcp_server])

    async def chat_with_repo(self, repository: str, question: str, github_token: str, messages: List[Dict[str, str]] = None) -> str:
        """
        Chat with a repository using the GitHub MCP server (Stdio).
        
        Args:
            repository: Full name of the repository (e.g., "owner/repo")
            question: The user's question
            github_token: The user's GitHub personal access token for the MCP server
            messages: List of previous messages in the conversation
            
        Returns:
            The AI's response as a clean string
        """
        try:
            # Validate the repository string format
            if not repository or not isinstance(repository, str) or '/' not in repository:
                logger.error(f"Invalid repository format received: {repository}")
                return "The repository name is not in the expected 'owner/repo' format. Please select the repository again or contact support if the issue persists."
            
            parts = repository.split('/', 1)
            owner = parts[0]
            repo_name = parts[1]

            if not owner or owner.lower() == "null" or owner.lower() == "undefined":
                logger.error(f"Invalid owner in repository string: {repository}")
                return f"The repository owner ('{owner}') appears to be invalid. Please select the repository again or contact support if the issue persists."
            if not repo_name: # Also check repo_name, though the error was with owner
                logger.error(f"Invalid repository name in repository string: {repository}")
                return "The repository name appears to be missing. Please select the repository again or contact support if the issue persists."

            logger.info(f"Attempting to use MCPServerStdio for repository: {repository}")
            
            # Construct a conversation string or a more structured input for the agent
            conversation_history = ""
            if messages:
                for msg in messages:
                    role = "User" if msg.get("role") == "user" else "Assistant"
                    conversation_history += f"{role}: {msg.get('content', '')}\n"
            
            full_query = f"Context: Repository '{repository}'.\n"
            if conversation_history:
                full_query += f"Conversation History:\n{conversation_history}\n"
            full_query += f"User Question: {question}"

            # Store original env and set the token for this specific call
            original_env = self.mcp_server.env
            self.mcp_server.env = {'GITHUB_PERSONAL_ACCESS_TOKEN': github_token}
            
            response_text = ""
            try:
                async with self.agent.run_mcp_servers(): 
                    result = await self.agent.run(full_query)
                response_text = self._extract_response_from_result(result)
            finally:
                # Restore original env
                self.mcp_server.env = original_env
                
            return response_text
            
        except Exception as e:
            logger.error(f"Error in AI service (chat_with_repo with MCPServerStdio): {str(e)}")
            return f"I encountered an error while processing your question with MCPServerStdio: {str(e)}"

    async def _prepare_repo_context(self, repo_name: str, github_token: str) -> str:
        """Prepare context information about the repository (can be used if needed, or let MCP tools handle it)"""
        try:
            repos = self.github_service.get_user_repositories(github_token)
            repo = next((r for r in repos if r.name == repo_name), None)
            
            if not repo:
                return f"Could not find repository {repo_name}."
            
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
        Prepare the complete prompt for the AI (can be used if needed, or let MCP tools handle it)
        """
        prompt = f"""You are an AI assistant specialized in analyzing GitHub repositories. 
Your task is to provide helpful information about the repository based on the user's questions.

{context}

"""
        if messages and len(messages) > 0:
            prompt += "Previous conversation:\n"
            for msg in messages:
                role = "User" if msg["role"] == "user" else "Assistant"
                prompt += f"{role}: {msg['content']}\n"
            
            prompt += "\n"
        
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