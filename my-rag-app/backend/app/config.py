from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Chroma configuration
    chroma_persist_dir: Path = Path("chroma_data")
    
    # API configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Development mode
    dev_mode: bool = False
    
    # Embedding model configuration
    embedding_model: str = "sentence-transformers/all-mpnet-base-v2"
    embedding_dim: int = 768
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


# Create a global settings instance
settings = Settings() 