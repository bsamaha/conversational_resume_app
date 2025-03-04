from fastapi import APIRouter, HTTPException
from app.schemas.query import SaveChatQuery
from app.services.s3_service import S3Service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Create an instance of the S3Service
s3_service = S3Service()

@router.post("/save-chat", status_code=200)
async def save_chat(query: SaveChatQuery):
    try:
        # Save the chat log to S3
        result = await s3_service.save_chat_log(
            session_id=query.session_id,
            user_info=query.user_info,
            messages=query.messages
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="Failed to save chat log to S3")
        
        return {"status": "success", "message": "Chat log saved successfully"}
    except Exception as e:
        logger.error(f"Error in save-chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 