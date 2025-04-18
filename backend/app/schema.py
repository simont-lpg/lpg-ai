from pydantic import BaseModel, Field, validator, StrictStr
from typing import Optional, Dict, List

class Document(BaseModel):
    """Document model for storing text content."""
    content: str
    meta: Dict = {}
    id: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert document to dictionary."""
        return {
            "content": self.content,
            "meta": self.meta,
            "id": self.id
        }

class Query(BaseModel):
    """Query model for RAG requests."""
    text: StrictStr = Field(alias="query", min_length=1)  # Allow 'query' field for backward compatibility
    top_k: int = Field(default=5, ge=1)

    @validator('text')
    def validate_text(cls, v):
        if not v.strip():
            raise ValueError("Query cannot be empty")
        return v

class Response(BaseModel):
    """Response model for RAG results."""
    answers: List[str]
    documents: List[Dict]  # Changed to List[Dict] to match the actual response format 