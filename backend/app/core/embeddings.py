from langchain_openai import OpenAIEmbeddings
from app.core.config import get_settings
from pydantic import SecretStr

settings = get_settings()

_embeddings = OpenAIEmbeddings(
    api_key=SecretStr(settings.openai_api_key),
    model=settings.embedding_model
)

async def get_embeddings(text: str) -> list[float]:
    """Generate embeddings for a given text using OpenAI's API."""
    embedding = await _embeddings.aembed_query(text)
    return embedding
