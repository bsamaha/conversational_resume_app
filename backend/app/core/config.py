from pydantic_settings import BaseSettings
from pydantic import validator
from functools import lru_cache
import os
import re
from typing import Optional, List, Dict, Any
import logging
import boto3

logger = logging.getLogger(__name__)

# List of supported OpenAI embedding models and their dimensions
EMBEDDING_MODELS = {
    "text-embedding-ada-002": 1536,
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072
}

def get_int_from_env(name: str, default: str) -> int:
    """Extract the first integer value from an environment variable or return the default."""
    value = os.getenv(name, default)
    if not value:
        return int(default)
    
    # Find the first sequence of digits
    match = re.search(r'\d+', value)
    if match:
        return int(match.group())
    
    return int(default)

class ParameterStoreConfig:
    """Handles retrieving configuration from AWS Parameter Store."""
    
    def __init__(self, region_name: Optional[str] = None):
        self.client = None
        self.cache: Dict[str, str] = {}
        self.region_name = region_name or os.environ.get("AWS_REGION", "us-east-2")
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize the AWS SSM client."""
        try:
            self.client = boto3.client('ssm', region_name=self.region_name)
            logger.info(f"Initialized AWS SSM client in region {self.region_name}")
        except Exception as e:
            logger.error(f"Failed to initialize AWS SSM client: {str(e)}")
            logger.warning("Falling back to environment variables for configuration")
    
    def get_parameter(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a parameter from AWS Parameter Store.
        Falls back to environment variables if Parameter Store is unavailable.
        """
        # Return from cache if available
        if name in self.cache:
            return self.cache[name]
        
        # If client initialization failed, fall back to environment variables
        if self.client is None:
            return os.environ.get(name, default)
        
        # Try to get from Parameter Store
        try:
            response = self.client.get_parameter(
                Name=name,
                WithDecryption=True
            )
            value = response['Parameter']['Value']
            # Cache the value
            self.cache[name] = value
            return value
        except Exception as e:
            logger.warning(f"Failed to get parameter {name} from Parameter Store: {str(e)}")
            logger.info(f"Falling back to environment variable for {name}")
            # Fall back to environment variables
            return os.environ.get(name, default)

class Settings(BaseSettings):
    """Application settings, with support for environment variables and Parameter Store."""
    
    # API settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # Database settings
    CHROMA_DB_PATH: str = "./data/chroma"
    
    # AWS settings
    AWS_REGION: str = "us-east-2"
    AWS_S3_BUCKET_NAME: Optional[str] = None
    CHAT_LOG_STORAGE_STRATEGY: str = "session-end"  # "session-end", "periodic", or "real-time"
    PERIODIC_STORAGE_INTERVAL: int = 300  # seconds, if using periodic strategy
    
    # Model settings
    MODEL_NAME: str = "gpt-3.5-turbo"
    EMBEDDING_MODEL: str = "text-embedding-ada-002"
    
    # Secret settings that will be fetched from Parameter Store in production
    OPENAI_API_KEY: Optional[str] = None
    AWS_ACCESS_KEY_ID: Optional[str] = None 
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    
    # Environment
    ENV: str = "development"  # "development", "staging", or "production"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Only use Parameter Store in production and staging
        if self.ENV in ("production", "staging"):
            self._load_from_parameter_store()
    
    def _load_from_parameter_store(self):
        """Load sensitive configuration from AWS Parameter Store."""
        try:
            store = ParameterStoreConfig(region_name=self.AWS_REGION)
            
            # Get secrets from Parameter Store
            self.OPENAI_API_KEY = store.get_parameter("OPENAI_API_KEY", self.OPENAI_API_KEY)
            self.AWS_ACCESS_KEY_ID = store.get_parameter("CONVERSATIONAL_RESUME_AWS_ACCESS_KEY_ID", self.AWS_ACCESS_KEY_ID)
            self.AWS_SECRET_ACCESS_KEY = store.get_parameter("CONVERSATIONAL_RESUME_AWS_ACCESS_KEY_SECRET", self.AWS_SECRET_ACCESS_KEY)
            
            logger.info("Successfully loaded secrets from AWS Parameter Store")
        except Exception as e:
            logger.error(f"Failed to load from Parameter Store: {str(e)}")
            logger.warning("Using values from environment variables instead")
    
    @validator('EMBEDDING_MODEL')
    def validate_embedding_model(cls, v):
        if v not in EMBEDDING_MODELS:
            raise ValueError(f"Embedding model {v} not supported. Choose from: {', '.join(EMBEDDING_MODELS.keys())}")
        return v
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of the current embedding model."""
        return EMBEDDING_MODELS.get(self.EMBEDDING_MODEL, 1536)

# Create global settings instance
settings = Settings()
