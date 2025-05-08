from typing import Dict, List
from pydantic import BaseModel


class QueryRequest(BaseModel):
    query: str

class ChatRequest(BaseModel):
    github_token: str
    question: str
    messages: List[Dict[str, str]]