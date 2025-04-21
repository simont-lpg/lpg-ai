from pydantic import BaseModel, Field, field_validator, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import List, Optional, Dict, Any
import os

class Settings(BaseSettings):
    """Settings for the application."""
    embedding_model: str = Field(
        default="all-MiniLM-L6-v2",
        description="Name of the embedding model to use"
    )
    embedding_model_name: str = Field(
        default="all-MiniLM-L6-v2",
        description="Display name of the embedding model"
    )
    embedding_dim: int = Field(
        default=384,
        gt=0,
        description="Embedding dimension must be positive"
    )
    ollama_api_url: HttpUrl = Field(
        default="http://127.0.0.1:11434",
        description="URL of the Ollama API"
    )
    collection_name: str = Field(
        default="documents",
        description="Name of the document collection"
    )
    dev_mode: bool = Field(
        default=False,
        description="Whether to run in development mode"
    )

    # API Configuration
    api_host: str = Field(
        default="0.0.0.0",
        description="Host to bind the API server to"
    )
    api_port: int = Field(
        default=8000,
        description="Port to bind the API server to"
    )
    
    # CORS Configuration
    cors_origins: List[str] = Field(
        default=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175"],
        description="Comma-separated list of allowed CORS origins"
    )

    # Environment-specific settings
    environment: str = Field(
        default="development",
        description="Current environment (development, production)"
    )
    
    # Logging configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    
    # Database configuration
    database_url: str = Field(
        default="sqlite:///./haystack.db",
        description="Database connection URL"
    )
    
    # Security settings
    secret_key: str = Field(
        default="your-secret-key-here",
        description="Secret key for JWT tokens"
    )
    
    # Rate limiting
    rate_limit_per_minute: int = Field(
        default=60,
        description="Maximum requests per minute"
    )

    @field_validator("cors_origins", mode="before")
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("ollama_api_url")
    def validate_ollama_url(cls, v: HttpUrl) -> HttpUrl:
        """Validate that the Ollama API URL uses http or https scheme."""
        if str(v).startswith(("http://", "https://")):
            return v
        raise ValueError("URL scheme should be 'http' or 'https'")

    def __hash__(self):
        """Make Settings hashable based on its field values."""
        return hash((
            self.embedding_model,
            self.embedding_model_name,
            self.embedding_dim,
            str(self.ollama_api_url),
            self.collection_name,
            self.dev_mode,
            self.api_host,
            self.api_port,
            tuple(self.cors_origins),
            self.environment,
            self.log_level,
            self.database_url,
            self.secret_key,
            self.rate_limit_per_minute
        ))

    def __eq__(self, other):
        """Compare Settings instances for equality."""
        if not isinstance(other, Settings):
            return False
        return (
            self.embedding_model == other.embedding_model and
            self.embedding_model_name == other.embedding_model_name and
            self.embedding_dim == other.embedding_dim and
            str(self.ollama_api_url) == str(other.ollama_api_url) and
            self.collection_name == other.collection_name and
            self.dev_mode == other.dev_mode and
            self.api_host == other.api_host and
            self.api_port == other.api_port and
            tuple(self.cors_origins) == tuple(other.cors_origins) and
            self.environment == other.environment and
            self.log_level == other.log_level and
            self.database_url == other.database_url and
            self.secret_key == other.secret_key and
            self.rate_limit_per_minute == other.rate_limit_per_minute
        )

    model_config = SettingsConfigDict(
        env_prefix="HAYSTACK_",
        env_file=".env",  # Default to .env
        env_file_encoding="utf-8",
        extra="ignore",  # Changed from "allow" to "ignore" for security
        case_sensitive=True,
        validate_default=True,
    )

    @classmethod
    def from_env_file(cls, env_file: str) -> "Settings":
        """Create settings from an environment file."""
        # Read environment file
        with open(env_file) as f:
            env_content = f.read()
        
        # Parse environment variables
        env_vars = {}
        for line in env_content.strip().split("\n"):
            if line and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                if key.startswith("HAYSTACK_"):
                    env_vars[key[9:].lower()] = value
        
        # Create settings with environment variables
        return cls(**env_vars)

@lru_cache()
def get_settings() -> Settings:
    """Get application settings with caching."""
    env_file = (
        ".env.production" if os.getenv("HAYSTACK_ENVIRONMENT") == "production"
        else ".env.development"
    )
    return Settings.from_env_file(env_file) if os.path.exists(env_file) else Settings()

# Initialize settings
settings = get_settings() 