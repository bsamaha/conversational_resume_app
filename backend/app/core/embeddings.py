from langchain_openai import OpenAIEmbeddings
from app.core.config import settings, EMBEDDING_MODELS
from pydantic import SecretStr
import logging

logger = logging.getLogger(__name__)

# Log information about the embedding model being used
logger.info(f"Using embedding model: {settings.EMBEDDING_MODEL}")
logger.info(f"Embedding dimensions: {EMBEDDING_MODELS[settings.EMBEDDING_MODEL]}")

# Validate API key
if not settings.OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set. Please set it in your environment variables or Parameter Store.")

# Initialize embeddings model
_embeddings = OpenAIEmbeddings(
    api_key=SecretStr(settings.OPENAI_API_KEY),
    model=settings.EMBEDDING_MODEL
)

async def get_embeddings(text: str) -> list[float]:
    """Generate embeddings for a given text using the configured OpenAI embedding model."""
    logger.info(f"Generating embeddings using model: {settings.EMBEDDING_MODEL}")
    embedding = await _embeddings.aembed_query(text)
    
    # Verify the embedding dimensions match what we expect
    expected_dim = settings.get_embedding_dimension()
    actual_dim = len(embedding)
    
    if actual_dim != expected_dim:
        logger.warning(
            f"Embedding dimension mismatch: expected {expected_dim}, got {actual_dim}. "
            f"This could cause issues with retrieval."
        )
    
    return embedding

async def get_document_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for multiple documents using the configured OpenAI embedding model.
    This is more efficient than calling get_embeddings() multiple times as it uses batching.
    """
    logger.info(f"Generating batch document embeddings using model: {settings.EMBEDDING_MODEL}")
    embeddings = await _embeddings.aembed_documents(texts)
    
    # Verify the embedding dimensions match what we expect
    if embeddings and len(embeddings) > 0:
        expected_dim = settings.get_embedding_dimension()
        actual_dim = len(embeddings[0])
        
        if actual_dim != expected_dim:
            logger.warning(
                f"Document embedding dimension mismatch: expected {expected_dim}, got {actual_dim}. "
                f"This could cause issues with retrieval."
            )
    
    return embeddings
