from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)


class Conversation(BaseModel):
    id: str
    repo_name: str
    messages: List[Message] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Repository(BaseModel):
    name: str
    full_name: str
    description: Optional[str] = None
    default_branch: str = "main"
    branches: List[str] = []
    last_active: Optional[str] = None


class QueryRequest(BaseModel):
    query: str


class ChatRequest(BaseModel):
    repository: str
    question: str
    messages: List[Dict[str, str]] = []  # Each message has 'role' and 'content'


class ChatResponse(BaseModel):
    response: str


class GitHubAuthRequest(BaseModel):
    github_token: str


class RepositoriesResponse(BaseModel):
    repositories: List[Repository]


class ChunkAnalysis(BaseModel):
    content_type: str
    context: str
    quality_score: float
    insights: str
    suggestions: str


class FileAnalysis(BaseModel):
    lint_score: float
    chunks: Dict[str, ChunkAnalysis]
    recent_changes: str
    insights: str
    suggestions: str
    repo_context: str


class CodeQualityResponse(BaseModel):
    overall_score: float
    file_analyses: Dict[str, FileAnalysis]
    summary: str


class AnalyzeRequest(BaseModel):
    repository: str