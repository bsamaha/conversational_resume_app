from typing import Optional, cast
from langchain_openai import ChatOpenAI
from app.core.config import settings
from app.core.vector_db import get_relevant_context
from app.core.prompt import get_chat_prompt
from fastapi import HTTPException
import os
from pydantic import SecretStr
import logging

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize chat model
def create_chat_model() -> ChatOpenAI:
    """Create a new instance of ChatOpenAI with proper configuration."""
    if not settings.OPENAI_API_KEY:
        raise ValueError("OpenAI API key not found in settings")
    
    return ChatOpenAI(
        temperature=0.2,
        model=settings.MODEL_NAME,
        api_key=SecretStr(settings.OPENAI_API_KEY)
    )

# Create a singleton instance
_chat_model: Optional[ChatOpenAI] = None

def get_chat_model() -> ChatOpenAI:
    """Get or create ChatOpenAI instance."""
    global _chat_model
    if _chat_model is None:
        _chat_model = create_chat_model()
    return cast(ChatOpenAI, _chat_model)

async def get_chat_response(message: str) -> str:
    """Get a chat response for the given message."""
    try:
        logger.info("Starting chat response generation for message: %s", message)
        chat_model = get_chat_model()

        logger.info("Attempting to retrieve relevant context from vector store")
        context = await get_relevant_context(message)
        logger.info("Retrieved context from vector store: %s", context)

        logger.info("Generating prompt with context")
        prompt = get_chat_prompt(context, message)
        logger.info("Generated prompt: %s", prompt)

        logger.info("Sending prompt to OpenAI")
        response = await chat_model.agenerate([prompt])
        result = response.generations[0][0].text
        logger.info("Received response from OpenAI: %s", result)

        return result
    except Exception as e:
        logger.error("Error in chat response generation", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error in chat response: {str(e)}"
        ) from e
