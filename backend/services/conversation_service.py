import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any
import json
import os
import logging
from models.pydantic_models import Conversation, Message

logger = logging.getLogger(__name__)

# In a production environment, this would use a database
# For simplicity, we'll use file-based storage
class ConversationService:
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        self.conversations_dir = os.path.join(self.data_dir, "conversations")
        
        # Ensure directories exist
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.conversations_dir, exist_ok=True)
        
    def create_conversation(self, repo_name: str) -> Conversation:
        """Create a new conversation for a repository"""
        conversation_id = str(uuid.uuid4())
        conversation = Conversation(
            id=conversation_id,
            repo_name=repo_name,
            messages=[],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Save the conversation
        self._save_conversation(conversation)
        
        return conversation
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation by ID"""
        try:
            file_path = os.path.join(self.conversations_dir, f"{conversation_id}.json")
            
            if not os.path.exists(file_path):
                return None
            
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            # Convert the raw data back to a Conversation object
            messages = [Message(**msg) for msg in data.get("messages", [])]
            
            conversation = Conversation(
                id=data["id"],
                repo_name=data["repo_name"],
                messages=messages,
                created_at=datetime.fromisoformat(data["created_at"]),
                updated_at=datetime.fromisoformat(data["updated_at"])
            )
            
            return conversation
        except Exception as e:
            logger.error(f"Error retrieving conversation {conversation_id}: {str(e)}")
            return None
    
    def add_message(self, conversation_id: str, role: str, content: str) -> Optional[Conversation]:
        """Add a message to a conversation"""
        conversation = self.get_conversation(conversation_id)
        
        if not conversation:
            return None
        
        # Add the new message
        message = Message(
            role=role,
            content=content,
            timestamp=datetime.now()
        )
        
        conversation.messages.append(message)
        conversation.updated_at = datetime.now()
        
        # Save the updated conversation
        self._save_conversation(conversation)
        
        return conversation
    
    def get_conversations_for_repo(self, repo_name: str) -> List[Conversation]:
        """Get all conversations for a specific repository"""
        conversations = []
        
        try:
            # List all conversation files
            for filename in os.listdir(self.conversations_dir):
                if filename.endswith(".json"):
                    file_path = os.path.join(self.conversations_dir, filename)
                    
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    
                    # Check if this conversation is for the requested repository
                    if data.get("repo_name") == repo_name:
                        messages = [Message(**msg) for msg in data.get("messages", [])]
                        
                        conversation = Conversation(
                            id=data["id"],
                            repo_name=data["repo_name"],
                            messages=messages,
                            created_at=datetime.fromisoformat(data["created_at"]),
                            updated_at=datetime.fromisoformat(data["updated_at"])
                        )
                        
                        conversations.append(conversation)
        except Exception as e:
            logger.error(f"Error retrieving conversations for repo {repo_name}: {str(e)}")
        
        # Sort conversations by updated_at (most recent first)
        conversations.sort(key=lambda x: x.updated_at, reverse=True)
        
        return conversations
    
    def _save_conversation(self, conversation: Conversation) -> None:
        """Save a conversation to the file system"""
        try:
            file_path = os.path.join(self.conversations_dir, f"{conversation.id}.json")
            
            # Convert datetime objects to ISO format strings for JSON serialization
            data = {
                "id": conversation.id,
                "repo_name": conversation.repo_name,
                "messages": [
                    {
                        "role": msg.role,
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat()
                    } for msg in conversation.messages
                ],
                "created_at": conversation.created_at.isoformat(),
                "updated_at": conversation.updated_at.isoformat()
            }
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving conversation {conversation.id}: {str(e)}")
    
    def format_messages_for_ai(self, conversation: Conversation) -> List[Dict[str, str]]:
        """Format conversation messages for the AI model"""
        return [
            {"role": msg.role, "content": msg.content}
            for msg in conversation.messages
        ]
    
    async def save_message(self, conversation_id: str, repo_name: str, role: str, content: str) -> Optional[Conversation]:
        """Save a message to a conversation asynchronously"""
        # Get or create conversation
        conversation = self.get_conversation(conversation_id)
        
        if not conversation:
            # Create a new conversation
            conversation = self.create_conversation(repo_name)
        
        # Add the new message
        message = Message(
            role=role,
            content=content,
            timestamp=datetime.now()
        )
        
        conversation.messages.append(message)
        conversation.updated_at = datetime.now()
        
        # Save the updated conversation
        self._save_conversation(conversation)
        
        return conversation 