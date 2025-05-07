from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional, List
from models.pydantic_models import Repository
from services.github_service import GitHubService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/repositories", tags=["repositories"])

async def get_github_service(github_token: str = Header(..., description="GitHub Personal Access Token")):
    """Dependency to get GitHub service from token"""
    service = GitHubService(github_token)
    if not service.validate_token():
        raise HTTPException(status_code=401, detail="Invalid GitHub token")
    return service

@router.get("", response_model=List[Repository])
async def get_repositories(github_service: GitHubService = Depends(get_github_service)):
    """Get all repositories for the authenticated user"""
    try:
        repositories = github_service.get_user_repositories()
        return repositories
    except Exception as e:
        logger.error(f"Error fetching repositories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{repo_name}/branches")
async def get_repository_branches(
    repo_name: str, 
    github_service: GitHubService = Depends(get_github_service)
):
    """Get all branches for a specific repository"""
    try:
        # Find the repository full name
        repos = github_service.get_user_repositories()
        repo = next((r for r in repos if r.name == repo_name), None)
        
        if not repo:
            raise HTTPException(status_code=404, detail=f"Repository {repo_name} not found")
            
        branches = github_service.get_repository_branches(repo.full_name)
        return {"branches": branches}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching branches: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{repo_name}/contents")
async def get_repository_contents(
    repo_name: str, 
    path: str = "", 
    branch: Optional[str] = None,
    github_service: GitHubService = Depends(get_github_service)
):
    """Get contents of a repository at a specific path and branch"""
    try:
        # Find the repository full name
        repos = github_service.get_user_repositories()
        repo = next((r for r in repos if r.name == repo_name), None)
        
        if not repo:
            raise HTTPException(status_code=404, detail=f"Repository {repo_name} not found")
            
        contents = github_service.get_repository_content(repo.full_name, path, branch)
        return {"contents": contents}
    except Exception as e:
        logger.error(f"Error fetching repository contents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{repo_name}/file")
async def get_file_content(
    repo_name: str, 
    file_path: str,
    branch: Optional[str] = None,
    github_service: GitHubService = Depends(get_github_service)
):
    """Get the content of a specific file in a repository"""
    try:
        # Find the repository full name
        repos = github_service.get_user_repositories()
        repo = next((r for r in repos if r.name == repo_name), None)
        
        if not repo:
            raise HTTPException(status_code=404, detail=f"Repository {repo_name} not found")
            
        content = github_service.get_file_content(repo.full_name, file_path, branch)
        
        if content is None:
            raise HTTPException(status_code=404, detail=f"File {file_path} not found or is not a file")
            
        return {"content": content}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching file content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 