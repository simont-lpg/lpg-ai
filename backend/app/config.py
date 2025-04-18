from pydantic import BaseModel, Field, field_validator, HttpUrl
from pydantic_settings import BaseSettings
from pydantic.v1 import validator
from functools import lru_cache

class Settings(BaseSettings):
    """Settings for the application."""
    embedding_model: str = Field(default="all-MiniLM-L6-v2")
    embedding_model_name: str = Field(default="all-MiniLM-L6-v2")
    embedding_dim: int = Field(default=384, gt=0, description="Embedding dimension must be positive")
    ollama_api_url: HttpUrl = Field(default="http://127.0.0.1:11434")
    collection_name: str = Field(default="documents")
    dev_mode: bool = Field(default=False)

    @field_validator("ollama_api_url")
    def validate_ollama_url(cls, v: HttpUrl) -> HttpUrl:
        """Validate that the Ollama API URL uses http or https scheme."""
        if str(v).startswith(("http://", "https://")):
            return v
        raise ValueError("URL scheme should be 'http' or 'https'")

    model_config = {
        "env_prefix": "HAYSTACK_",
        "env_file": ".env",
        "extra": "allow"
    }

@lru_cache()
def get_settings() -> Settings:
    """Get application settings with caching."""
    return Settings() 