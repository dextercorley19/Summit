from fastapi import APIRouter, HTTPException, Depends, Header, Request
from typing import Optional, List
from models.pydantic_models import Repository, RepositoriesResponse
from services.github_service import GitHubService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/repositories", tags=["repositories"])

async def get_validated_token_and_service(request: Request, authorization: str = Header(None, alias="Authorization")):
    """Dependency to get GitHub service and validated token from Authorization or X-GitHub-Token header"""
    github_token = None
    if authorization and authorization.startswith("Bearer "):
        github_token = authorization.split(" ")[1]
    
    if not github_token:
        github_token = request.headers.get("X-GitHub-Token")

    if not github_token:
        raise HTTPException(status_code=401, detail="GitHub token not provided in Authorization (Bearer) header or X-GitHub-Token header")
    
    service = GitHubService()
    if not service.validate_token(github_token):
        raise HTTPException(status_code=401, detail="Invalid GitHub token")
    return service, github_token

@router.get("", response_model=RepositoriesResponse)
async def get_repositories(service_and_token: tuple = Depends(get_validated_token_and_service)):
    """Get all repositories for the authenticated user"""
    github_service, github_token = service_and_token
    try:
        repositories = github_service.get_user_repositories(github_token=github_token)
        return RepositoriesResponse(repositories=repositories)
    except Exception as e:
        logger.error(f"Error fetching repositories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{repo_name}/branches")
async def get_repository_branches(
    repo_name: str, 
    service_and_token: tuple = Depends(get_validated_token_and_service)
):
    """Get all branches for a specific repository"""
    github_service, github_token = service_and_token
    try:
        repos = github_service.get_user_repositories(github_token=github_token)
        repo = next((r for r in repos if r.name == repo_name), None)
        
        if not repo:
            raise HTTPException(status_code=404, detail=f"Repository {repo_name} not found")
            
        branches = github_service.get_repository_branches(repo.full_name, github_token=github_token)
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
    service_and_token: tuple = Depends(get_validated_token_and_service)
):
    """Get contents of a repository at a specific path and branch"""
    github_service, github_token = service_and_token
    try:
        repos = github_service.get_user_repositories(github_token=github_token)
        repo = next((r for r in repos if r.name == repo_name), None)
        
        if not repo:
            raise HTTPException(status_code=404, detail=f"Repository {repo_name} not found")
            
        contents = github_service.get_repository_content(repo.full_name, path, branch, github_token=github_token)
        return {"contents": contents}
    except Exception as e:
        logger.error(f"Error fetching repository contents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{repo_name}/file")
async def get_file_content(
    repo_name: str, 
    file_path: str,
    branch: Optional[str] = None,
    service_and_token: tuple = Depends(get_validated_token_and_service)
):
    """Get the content of a specific file in a repository"""
    github_service, github_token = service_and_token
    try:
        repos = github_service.get_user_repositories(github_token=github_token)
        repo = next((r for r in repos if r.name == repo_name), None)
        
        if not repo:
            raise HTTPException(status_code=404, detail=f"Repository {repo_name} not found")
            
        content = github_service.get_file_content(repo.full_name, file_path, branch, github_token=github_token)
        
        if content is None:
            raise HTTPException(status_code=404, detail=f"File {file_path} not found or is not a file")
            
        return {"content": content}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching file content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))