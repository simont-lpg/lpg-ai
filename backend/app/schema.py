from pydantic import BaseModel, Field, field_validator, StrictStr, ConfigDict
from typing import Optional, Dict, List, Any

class Document(BaseModel):
    """Document model for storing text content."""
    model_config = ConfigDict(arbitrary_types_allowed=True, extra='allow')
    
    content: str
    meta: Dict = {}
    id: Optional[str] = None
    embedding: Optional[List[float]] = None
    score: Optional[float] = None

    def to_dict(self) -> Dict:
        """Convert document to dictionary."""
        return {
            "content": self.content,
            "meta": self.meta,
            "id": self.id,
            "embedding": self.embedding,
            "score": self.score
        }

class Query(BaseModel):
    """Query model for RAG requests."""
    model_config = ConfigDict(arbitrary_types_allowed=True, extra='allow')
    
    text: StrictStr = Field(alias="query", min_length=1)  # Allow 'query' field for backward compatibility
    top_k: int = Field(default=5, ge=1)

    @field_validator('text')
    @classmethod
    def validate_text(cls, v):
        if not v.strip():
            raise ValueError("Query cannot be empty")
        return v

class Response(BaseModel):
    """Response model for RAG results."""
    model_config = ConfigDict(arbitrary_types_allowed=True, extra='allow')
    
    answers: List[str]
    documents: List[Dict[str, Any]]  # Changed to List[Dict] to match the actual response format 