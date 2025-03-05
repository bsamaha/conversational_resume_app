from langchain_openai import OpenAIEmbeddings
from app.core.config import get_settings, SUPPORTED_EMBEDDING_MODELS
from pydantic import SecretStr
import logging

settings = get_settings()
logger = logging.getLogger(__name__)

# Log information about the embedding model being used
embedding_info = settings.get_embedding_info()
logger.info(f"Using embedding model: {settings.embedding_model}")
logger.info(f"Embedding dimensions: {embedding_info['dimensions']}")
logger.info(f"Model details: {embedding_info['description']}")

# Initialize embeddings model
_embeddings = OpenAIEmbeddings(
    api_key=SecretStr(settings.openai_api_key),
    model=settings.embedding_model
)

async def get_embeddings(text: str) -> list[float]:
    """Generate embeddings for a given text using the configured OpenAI embedding model."""
    logger.info(f"Generating embeddings using model: {settings.embedding_model}")
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
    logger.info(f"Generating batch document embeddings using model: {settings.embedding_model}")
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
