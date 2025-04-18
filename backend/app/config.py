from pydantic import BaseSettings

class Settings(BaseSettings):
    """Application settings."""
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chroma_db_path: str = "data/chroma"
    vectorstore_type: str = "chroma"
    chroma_collection_name: str = "documents"
    dev_mode: bool = False
    
    class Config:
        env_prefix = "HAYSTACK_" 