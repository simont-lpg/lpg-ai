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

    def __hash__(self):
        """Make Settings hashable based on its field values."""
        return hash((
            self.embedding_model,
            self.embedding_model_name,
            self.embedding_dim,
            str(self.ollama_api_url),
            self.collection_name,
            self.dev_mode
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
            self.dev_mode == other.dev_mode
        )

    model_config = {
        "env_prefix": "HAYSTACK_",
        "env_file": ".env",
        "extra": "allow"
    }

@lru_cache()
def get_settings() -> Settings:
    """Get application settings with caching."""
    return Settings() 