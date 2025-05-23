from fastapi import APIRouter, HTTPException, BackgroundTasks, Request, Header
from models.pydantic_models import ChatRequest, ChatResponse
from services.ai_service import AIService
from services.conversation_service import ConversationService
import logging
import uuid
import re

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])
conversation_service = ConversationService()

@router.post("", response_model=ChatResponse)
async def chat_with_repository(request: ChatRequest, request_obj: Request, authorization: str = Header(None, alias="Authorization")):
    """
    Chat with a GitHub repository using AI
    """
    try:
        github_token = None
        if authorization and authorization.startswith("Bearer "):
            github_token = authorization.split(" ")[1]
        
        if not github_token:
            # Fallback to X-GitHub-Token if Authorization is not present or malformed, for backward compatibility or other clients
            github_token = request_obj.headers.get("X-GitHub-Token")

        if not github_token:
            raise HTTPException(status_code=401, detail="GitHub token not provided in Authorization (Bearer) header or X-GitHub-Token header")
            
        ai_service = AIService()
        
        conversation_id = request.conversation_id
        messages = request.messages

        if conversation_id:
            conversation = conversation_service.get_conversation(conversation_id)
            if conversation:
                messages = [msg.model_dump() for msg in conversation.messages] # Use model_dump()
            else: # If conversation_id is provided but not found, treat as a new conversation
                conversation_id = None 
        
        if not conversation_id: # Create a new conversation if no ID or not found
            conversation_id = str(uuid.uuid4())

        # Add current question to messages for AI service
        current_messages_for_ai = messages + [{"role": "user", "content": request.question}]

        # Get response from AI with conversation history
        result = await ai_service.chat_with_repo(
            repository=request.repository,
            question=request.question, # Still pass the individual question for context if needed by the AI service
            github_token=github_token,
            messages=current_messages_for_ai # Pass the full history
        )
        
        # Extract the actual response content from RunResult if needed
        if isinstance(result, str):
            clean_response = result
        else:
            # Try to get content from the response object
            if hasattr(result, '_all_messages'):
                raw_messages = result._all_messages
                if len(raw_messages) > 0:
                    last_message = raw_messages[-1]
                    if hasattr(last_message, 'parts') and len(last_message.parts) > 0:
                        last_part = last_message.parts[-1]
                        if hasattr(last_part, 'content'):
                            clean_response = last_part.content
                            # Save conversation
                            conversation_service.add_message_to_conversation(
                                conversation_id=conversation_id,
                                repo_name=request.repository,
                                role="user",
                                content=request.question
                            )
                            conversation_service.add_message_to_conversation(
                                conversation_id=conversation_id,
                                repo_name=request.repository,
                                role="assistant",
                                content=clean_response
                            )
                            return ChatResponse(response=clean_response, conversation_id=conversation_id)
            
            # If that fails, try regex patterns
            result_str = str(result)
            
            # Try to find content in TextPart
            content_match = re.search(r"TextPart\(content=['\"]([^'\"]*)['\"]", result_str)
            if content_match:
                clean_response = content_match.group(1)
            # Try to find content in data field
            elif data_match := re.search(r"data=['\"]([^'\"]*)['\"]", result_str):
                clean_response = data_match.group(1)
            # Try to find any quoted content
            elif quote_match := re.search(r"content=['\"]([^'\"]*)['\"]", result_str):
                clean_response = quote_match.group(1)
            else:
                clean_response = "I cannot verify the requested information in the repository."
        
        # Log the processed response for debugging
        logger.info(f"Processed AI response: {clean_response}")

        # Save conversation for all other cases
        conversation_service.add_message_to_conversation(
            conversation_id=conversation_id,
            repo_name=request.repository,
            role="user",
            content=request.question
        )
        conversation_service.add_message_to_conversation(
            conversation_id=conversation_id,
            repo_name=request.repository,
            role="assistant",
            content=clean_response
        )
        
        return ChatResponse(response=clean_response, conversation_id=conversation_id)
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{repo_name}")
async def get_conversation_history(repo_name: str):
    """Get conversation history for a repository"""
    try:
        conversations = conversation_service.get_conversations_for_repo(repo_name)
        
        # Convert conversations to a simpler format for the frontend
        response = [
            {
                "id": conv.id,
                "repo_name": conv.repo_name,
                "created_at": conv.created_at.isoformat(),
                "updated_at": conv.updated_at.isoformat(),
                "message_count": len(conv.messages),
                "last_message": conv.messages[-1].content if conv.messages else None
            }
            for conv in conversations
        ]
        
        return response
    except Exception as e:
        logger.error(f"Error retrieving conversation history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get a specific conversation by ID"""
    try:
        conversation = conversation_service.get_conversation(conversation_id)
        
        if not conversation:
            raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found")
            
        # Convert to a format suitable for the frontend
        messages = [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat()
            }
            for msg in conversation.messages
        ]
        
        return {
            "id": conversation.id,
            "repo_name": conversation.repo_name,
            "messages": messages,
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))