import requests
from typing import List, Dict, Any, Optional
import logging
from models.pydantic_models import Repository

logger = logging.getLogger(__name__)

class GitHubService:
    BASE_URL = "https://api.github.com"

    def __init__(self):
        pass

    def _get_headers(self, github_token: str) -> Dict[str, str]:
        return {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def validate_token(self, github_token: str) -> bool:
        """Validate if the GitHub token is valid"""
        headers = self._get_headers(github_token)
        try:
            response = requests.get(f"{self.BASE_URL}/user", headers=headers)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error validating GitHub token: {str(e)}")
            return False

    def get_user_repositories(self, github_token: str) -> List[Repository]:
        """Get all repositories for the authenticated user"""
        headers = self._get_headers(github_token)
        try:
            response = requests.get(f"{self.BASE_URL}/user/repos", headers=headers)
            
            if response.status_code != 200:
                logger.error(f"Error fetching repositories: {response.status_code} - {response.text}")
                return []
            
            repos_data = response.json()
            repositories = []
            
            for repo_data in repos_data:
                # Get branches for each repository
                branches = self.get_repository_branches(repo_data["full_name"], github_token)
                
                # Extract owner information
                owner_login = repo_data.get("owner", {}).get("login")
                if not owner_login:
                    logger.warning(f"Owner login not found for repo: {repo_data['full_name']}. Skipping.")
                    continue # Skip this repository if owner can't be determined

                repo = Repository(
                    name=repo_data["name"],
                    full_name=repo_data["full_name"],
                    owner=owner_login, # Populate the owner field
                    description=repo_data.get("description"),
                    default_branch=repo_data.get("default_branch", "main"),
                    branches=branches,
                    last_active=repo_data.get("updated_at", "Unknown")
                )
                repositories.append(repo)
                
            return repositories
        except Exception as e:
            logger.error(f"Error fetching repositories: {str(e)}")
            return []

    def get_repository_branches(self, repo_full_name: str, github_token: str) -> List[str]:
        """Get all branches for a specific repository"""
        headers = self._get_headers(github_token)
        try:
            response = requests.get(
                f"{self.BASE_URL}/repos/{repo_full_name}/branches",
                headers=headers
            )
            
            if response.status_code != 200:
                logger.error(f"Error fetching branches: {response.status_code} - {response.text}")
                return []
            
            branches_data = response.json()
            return [branch["name"] for branch in branches_data]
        except Exception as e:
            logger.error(f"Error fetching branches: {str(e)}")
            return []

    def get_repository_content(self, repo_full_name: str, path: str = "", branch: str = None, github_token: str = None) -> List[Dict[str, Any]]:
        """Get contents of a repository at a specific path and branch"""
        headers = self._get_headers(github_token)
        try:
            url = f"{self.BASE_URL}/repos/{repo_full_name}/contents/{path}"
            if branch:
                url += f"?ref={branch}"
                
            response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                logger.error(f"Error fetching repository content: {response.status_code} - {response.text}")
                return []
            
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching repository content: {str(e)}")
            return []

    def get_file_content(self, repo_full_name: str, file_path: str, branch: str = None, github_token: str = None) -> Optional[str]:
        """Get the content of a specific file in a repository"""
        headers = self._get_headers(github_token)
        try:
            url = f"{self.BASE_URL}/repos/{repo_full_name}/contents/{file_path}"
            if branch:
                url += f"?ref={branch}"
                
            response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                logger.error(f"Error fetching file content: {response.status_code} - {response.text}")
                return None
            
            content_data = response.json()
            if content_data.get("type") != "file":
                return None
            
            # GitHub API returns content as base64 encoded
            import base64
            if content_data.get("encoding") == "base64" and content_data.get("content"):
                return base64.b64decode(content_data["content"]).decode('utf-8')
            
            return None
        except Exception as e:
            logger.error(f"Error fetching file content: {str(e)}")
            return None