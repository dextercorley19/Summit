from fastapi import APIRouter, HTTPException
from models.pydantic_models import GitHubAuthRequest, RepositoriesResponse
from services.github_service import GitHubService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/github", response_model=RepositoriesResponse)
async def github_auth(request: GitHubAuthRequest):
    """
    Authenticate with GitHub using a personal access token.
    This will validate the token and return a list of repositories.
    """
    try:
        github_service = GitHubService(request.github_token)
        
        # Validate the token
        if not github_service.validate_token():
            raise HTTPException(status_code=401, detail="Invalid GitHub token")
        
        # Get repositories for the authenticated user
        repositories = github_service.get_user_repositories()
        
        return {"repositories": repositories}
    except Exception as e:
        logger.error(f"Error in GitHub authentication: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 