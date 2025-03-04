from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
import os
import re
from typing import Optional

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
    embedding_model: str = "text-embedding-ada-002"
    
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
        embedding_model=os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        aws_region=os.getenv("AWS_REGION"),
        aws_s3_bucket_name=os.getenv("AWS_S3_BUCKET_NAME"),
        chat_log_storage_strategy=os.getenv("CHAT_LOG_STORAGE_STRATEGY", "session-end"),
        periodic_storage_interval=periodic_interval
    )
