from pydantic_settings import BaseSettings
from pydantic import Field, validator
from functools import lru_cache
import os
import re
from typing import Optional, List, Dict, Any

# List of supported OpenAI embedding models and their dimensions
SUPPORTED_EMBEDDING_MODELS: Dict[str, Dict[str, Any]] = {
    "text-embedding-3-small": {
        "dimensions": 1536,
        "max_input_tokens": 8191,
        "description": "Most cost-effective, 62.3% performance on MTEB, ~62,500 pages per dollar"
    },
    "text-embedding-3-large": {
        "dimensions": 3072,
        "max_input_tokens": 8191,
        "description": "Highest performance, 64.6% on MTEB, ~9,615 pages per dollar"
    },
    "text-embedding-ada-002": {
        "dimensions": 1536,
        "max_input_tokens": 8191,
        "description": "Legacy model, 61.0% on MTEB, ~12,500 pages per dollar"
    }
}

def get_int_from_env(name: str, default: str) -> int:
    """Extract the first integer value from an environment variable or return the default."""
    value = os.getenv(name, default)
    if not value:
        return int(default)
    
    # Find the first sequence of digits
    match = re.search(r'\d+', value)
    if match:
        return int(match.group(0))
    return int(default)

class Settings(BaseSettings):
    # OpenAI Settings
    openai_api_key: str
    chroma_db_path: str = "./data/chroma"
    model_name: str = "gpt-3.5-turbo"
    
    # Embedding model settings - using text-embedding-3-small as default
    # Based on OpenAI documentation, this is the most cost-effective model
    # with good performance (62.3% on MTEB eval) and high token efficiency (~62,500 pages per dollar)
    embedding_model: str = "text-embedding-3-small"
    
    # AWS Settings
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: Optional[str] = None
    aws_s3_bucket_name: Optional[str] = None
    chat_log_storage_strategy: str = "session-end"  # or "periodic" or "real-time"
    periodic_storage_interval: int = 300  # seconds, if using periodic strategy
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        env_file_encoding = 'utf-8'
    
    @validator('embedding_model')
    def validate_embedding_model(cls, v):
        """Validate that the embedding model is supported."""
        if v not in SUPPORTED_EMBEDDING_MODELS:
            supported_models = ", ".join(SUPPORTED_EMBEDDING_MODELS.keys())
            raise ValueError(
                f"Embedding model '{v}' is not supported. "
                f"Supported models are: {supported_models}"
            )
        return v
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of the configured embedding model."""
        return SUPPORTED_EMBEDDING_MODELS[self.embedding_model]["dimensions"]
    
    def get_embedding_info(self) -> Dict[str, Any]:
        """Get information about the configured embedding model."""
        return SUPPORTED_EMBEDDING_MODELS[self.embedding_model]

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    
    # Convert PERIODIC_STORAGE_INTERVAL to int, stripping any comments
    periodic_interval_str = os.getenv("PERIODIC_STORAGE_INTERVAL", "300")
    if periodic_interval_str:
        periodic_interval = get_int_from_env("PERIODIC_STORAGE_INTERVAL", "300")
    else:
        periodic_interval = 300
    
    return Settings(
        openai_api_key=api_key,
        chroma_db_path=os.getenv("CHROMA_DB_PATH", "./data/chroma"),
        model_name=os.getenv("MODEL_NAME", "gpt-3.5-turbo"),
        embedding_model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        aws_region=os.getenv("AWS_REGION"),
        aws_s3_bucket_name=os.getenv("AWS_S3_BUCKET_NAME"),
        chat_log_storage_strategy=os.getenv("CHAT_LOG_STORAGE_STRATEGY", "session-end"),
        periodic_storage_interval=periodic_interval
    )
