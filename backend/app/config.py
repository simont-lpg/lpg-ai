from pydantic import Field, AnyUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import List, Dict, Any
import logging
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """Settings for the application."""
    # Model Settings
    embedding_model: str = Field(..., description="Name of the embedding model")
    generator_model_name: str = Field(..., description="Name of the generator model")
    embedding_dim: int = Field(default=1024, description="Dimension of the embeddings")
    ollama_api_url: AnyUrl = Field(..., description="URL of the Ollama API")
    
    # Document Store Settings
    collection_name: str = Field(..., description="Name of the document collection")
    
    # API Settings
    api_host: str = Field(..., description="Host to bind the API server to")
    api_port: int = Field(..., description="Port to bind the API server to")
    cors_origins: List[str] = Field(..., description="Comma-separated list of allowed CORS origins")
    
    # Environment Settings
    dev_mode: bool = Field(..., description="Whether to run in development mode")
    environment: str = Field(..., description="Current environment (development, production)")
    log_level: str = Field(..., description="Logging level")
    
    # Database Settings
    database_url: str = Field(..., description="Database connection URL")
    
    # Security Settings
    secret_key: str = Field(..., description="Secret key for JWT tokens")
    rate_limit_per_minute: int = Field(..., description="Maximum requests per minute")
    
    # Pipeline Settings
    default_top_k: int = Field(default=5, description="Default number of documents to retrieve")
    prompt_template: str = Field(
        default="""Based on the following context, please answer the question. If the answer cannot be found in the context, say "I don't know."

Context:
{context}

Question: {query}

Answer:""",
        description="Template for the prompt used in the pipeline"
    )
    pipeline_parameters: Dict[str, Any] = Field(
        default_factory=lambda: {
            "Retriever": {
                "top_k": 5,
                "score_threshold": 0.7
            },
            "Generator": {
                "temperature": 0.7,
                "max_tokens": 1000
            }
        },
        description="Default parameters for pipeline components"
    )

    @field_validator("embedding_dim")
    def validate_embedding_dim(cls, v: int) -> int:
        """Validate that embedding dimension is positive."""
        if v <= 0:
            raise ValueError("embedding_dim must be greater than 0")
        return v

    @field_validator("cors_origins", mode="before")
    def parse_cors_origins(cls, v):
        logger.info("Parsing CORS origins: %s", v)
        if isinstance(v, str):
            try:
                # Try to parse as JSON first
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                # If not JSON, split by comma
                return [origin.strip() for origin in v.split(",")]
        elif isinstance(v, list):
            return v
        else:
            logger.error("Invalid CORS origins format: %s", v)
            raise ValueError("CORS origins must be a JSON array or comma-separated string")

    @field_validator("ollama_api_url")
    def validate_ollama_url(cls, v: AnyUrl) -> AnyUrl:
        """Validate that the Ollama API URL uses http or https scheme."""
        if str(v).startswith(("http://", "https://")):
            return v
        raise ValueError("URL scheme should be 'http' or 'https'")

    def __hash__(self):
        """Make Settings hashable based on its field values."""
        # Convert dictionaries to tuples of sorted items
        pipeline_params = tuple(
            (k, tuple(sorted(v.items()))) 
            for k, v in sorted(self.pipeline_parameters.items())
        )
        
        return hash((
            self.embedding_model,
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
            self.rate_limit_per_minute,
            self.generator_model_name,
            self.default_top_k,
            self.prompt_template,
            pipeline_params
        ))

    def __eq__(self, other):
        """Compare Settings instances for equality."""
        if not isinstance(other, Settings):
            return False
        return (
            self.embedding_model == other.embedding_model and
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
            self.rate_limit_per_minute == other.rate_limit_per_minute and
            self.generator_model_name == other.generator_model_name and
            self.default_top_k == other.default_top_k and
            self.prompt_template == other.prompt_template and
            self.pipeline_parameters == other.pipeline_parameters
        )

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent / ".env"),
        env_prefix="LPG_AI_",
        env_file_encoding="utf-8",
    )

@lru_cache()
def get_settings() -> Settings:
    """Get application settings with caching."""
    settings = Settings()
    logger.info("Settings loaded with values:")
    for key, value in settings.model_dump().items():
        if key not in ["secret_key"]:  # Don't log sensitive information
            logger.info(f"  {key}: {value}")
    return settings

# Initialize settings
settings = get_settings() 