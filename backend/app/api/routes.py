from fastapi import APIRouter
from app.api.routers import chat_router, save_chat_router

# Create main API router
api_router = APIRouter()

# Include all sub-routers
api_router.include_router(chat_router)
api_router.include_router(save_chat_router) 