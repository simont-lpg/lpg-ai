from pydantic import BaseModel, Field, field_validator, StrictStr, ConfigDict
from typing import Optional, Dict, List, Any
import numpy as np

class DocumentMetadataResponse(BaseModel):
    """Response model for document metadata without content."""
    id: Optional[str] = None
    meta: Dict = {}

    model_config = ConfigDict(arbitrary_types_allowed=True, extra='allow')

class DocumentMetadata(BaseModel):
    """Document metadata model."""
    id: str
    meta: Dict[str, Any]
    content: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "meta": self.meta,
            "content": self.content
        }

class DocumentFull(DocumentMetadata):
    """Full document model including embeddings and scores."""
    embedding: Optional[List[float]] = None
    score: Optional[float] = None

    def to_dict(self) -> Dict:
        """Convert document to dictionary."""
        base_dict = {
            "meta": self.meta,
            "id": self.id,
            "content": self.content
        }
        if self.embedding is not None:
            if isinstance(self.embedding, np.ndarray):
                base_dict["embedding"] = self.embedding.tolist()
            else:
                base_dict["embedding"] = self.embedding
        if self.score is not None:
            base_dict["score"] = float(self.score)
        return base_dict

    model_config = ConfigDict(arbitrary_types_allowed=True)

class Query(BaseModel):
    """Query model for RAG queries."""
    text: StrictStr = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=100)
    namespace: Optional[str] = Field(default=None, description="Optional namespace to filter documents")
    file_id: Optional[str] = Field(default=None, description="Optional file ID to filter documents")

class Response(BaseModel):
    """Response model for RAG queries."""
    answers: List[str] = Field(default_factory=list)
    documents: List[Dict[str, Any]] = Field(default_factory=list)
    error: Optional[str] = Field(default=None, description="Error message if query failed")

class DeleteDocumentsRequest(BaseModel):
    """Request model for deleting documents by file name."""
    file_name: str

class DeleteDocumentsResponse(BaseModel):
    """Response model for document deletion."""
    status: str = "success"
    deleted: int

class FileMetadata(BaseModel):
    """Metadata for a file in the document store."""
    filename: str
    namespace: str = "default"
    document_count: int
    id: str
    file_size: int  # Size in bytes

class FileListResponse(BaseModel):
    """Response model for the /files endpoint."""
    files: List[FileMetadata] 