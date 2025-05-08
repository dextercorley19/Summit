from fastapi import APIRouter, HTTPException, Request, Header
from models.pydantic_models import AnalyzeRequest, CodeQualityResponse, FileAnalysis, ChunkAnalysis
import logging
import json
from pydantic import ValidationError
from services.ai_service import AIService
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analyze", tags=["analysis"])
ai_service = AIService()

@router.post("", response_model=CodeQualityResponse)
async def analyze_repository(request: AnalyzeRequest, request_obj: Request, authorization: str = Header(None, alias="Authorization")):
    """
    Analyze a GitHub repository for code quality.
    """
    try:
        github_token = None
        if authorization and authorization.startswith("Bearer "):
            github_token = authorization.split(" ")[1]

        if not github_token:
            # Fallback to GitHub-Token if Authorization is not present or malformed
            github_token = request_obj.headers.get("GitHub-Token")

        if not github_token:
            raise HTTPException(status_code=401, detail="GitHub token not provided in Authorization header or GitHub-Token header")

        logger.info(f"Received analysis request for repository: {request.repository}")

        # Define the detailed prompt for the AI
        analysis_prompt = f"""Please analyze the GitHub repository '{request.repository}'.
Provide a comprehensive code quality analysis. I need the output in a structured JSON format that strictly adheres to the following Pydantic model:

```json
{{
    "overall_score": "float (e.g., 7.8)",
    "file_analyses": {{
        "filename_or_path_as_key": {{
            "lint_score": "float (e.g., 8.5)",
            "chunks": {{
                "chunk_name_or_identifier": {{
                    "content_type": "string (e.g., 'function', 'class', 'method', 'block')",
                    "context": "string (actual code snippet or relevant context)",
                    "quality_score": "float (e.g., 9.0)",
                    "insights": "string (AI-generated insights about this chunk)",
                    "suggestions": "string (AI-generated suggestions for this chunk)"
                }}
                // ... more chunks if applicable
            }},
            "recent_changes": "string (summary of recent changes if available, otherwise empty string)",
            "insights": "string (overall insights for this file)",
            "suggestions": "string (overall suggestions for this file)",
            "repo_context": "string (context of this file within the repository)"
        }}
        // ... more files if applicable
    }},
    "summary": "string (a general summary of the repository's code quality, including overall strengths and weaknesses)"
}}
```

Focus on identifying areas for improvement, potential bugs, code smells, and adherence to best practices.
For each file, provide specific insights and actionable suggestions.
If possible, break down the analysis by relevant code chunks (functions, classes, methods).
The 'overall_score' should be a float between 0.0 and 10.0, representing the perceived quality.
'lint_score' and 'quality_score' for chunks should also be floats between 0.0 and 10.0.
Ensure the entire response is a single JSON object. Do not include any explanatory text outside of this JSON structure.
"""

        ai_response_str = await ai_service.chat_with_repo(
            repository=request.repository,
            question=analysis_prompt,
            github_token=github_token,
            messages=[] # No prior messages for a new analysis
        )

        logger.debug(f"Raw AI response for analysis: {ai_response_str}")

        # Attempt to parse the AI's response string into the CodeQualityResponse model
        try:
            # Basic extraction of JSON block if AI includes surrounding text
            if "```json" in ai_response_str:
                json_block = ai_response_str.split("```json")[1].split("```")[0].strip()
            elif "```" in ai_response_str: # if only ``` is present
                 json_block = ai_response_str.split("```")[1].split("```")[0].strip()
            else:
                json_block = ai_response_str

            parsed_response = json.loads(json_block)
            response_data = CodeQualityResponse(**parsed_response)
            return response_data
        except (json.JSONDecodeError, ValidationError, IndexError) as e:
            logger.error(f"Failed to parse AI response into CodeQualityResponse: {str(e)}. Raw response: {ai_response_str}")
            # Fallback: return the raw AI response in the summary or a custom error message
            return CodeQualityResponse(
                overall_score=0.0,
                file_analyses={},
                summary=f"Error processing AI analysis. Raw AI output: {ai_response_str}"
            )

    except HTTPException as http_exc:
        logger.error(f"HTTPException in analyze endpoint: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"Error in analyze endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
