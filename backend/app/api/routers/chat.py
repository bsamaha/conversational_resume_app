from fastapi import APIRouter, HTTPException
from app.schemas.query import ChatRequestDto
from app.schemas.response import ChatResponse
from app.core.chat_chain import chat_invoke
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequestDto):
    logger.info(f"Received chat request with query={request.query}, thread_id={request.thread_id}")
    try:
        answer = chat_invoke(request.query, request.language, request.thread_id)
        # Safely extract text and force convert to string
        if isinstance(answer, str):
            response_text = answer
        elif not isinstance(answer, str) and hasattr(answer, "content"):
            response_text = str(answer.content)
        else:
            response_text = str(answer)
        logger.info(f"Chat response: {response_text}")
        return ChatResponse(response=response_text)
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 