import os
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import openai

from app.api.routes import api_router
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize OpenAI with API key from settings
openai.api_key = settings.OPENAI_API_KEY

# Initialize FastAPI app
app = FastAPI(
    title="Conversational Resume API",
    description="API for the Conversational Resume & Portfolio Chatbot",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")

# Root endpoint
@app.get("/")
async def root():
    """Welcome endpoint"""
    return {"message": "Welcome to the Conversational Resume Chatbot API"}

# Ping endpoint for simple availability check
@app.get("/ping")
async def ping():
    """Simple ping-pong check"""
    return {"message": "pong"}

# Health check endpoint
@app.get("/health")
async def health_check():
    """Check if the API is running"""
    return {"status": "healthy"}

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log incoming requests and their responses"""
    logger.info(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Completed request: {request.method} {request.url} with status {response.status_code}")
    return response

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": "An unexpected error occurred. Please try again later."},
    )

# Log app startup with configuration information
@app.on_event("startup")
async def startup_event():
    env_info = "production" if settings.ENV in ("production", "staging") else "development"
    config_source = "Parameter Store" if settings.ENV in ("production", "staging") else "environment variables"
    
    logger.info(f"Starting application in {env_info} mode")
    logger.info(f"Using configuration from {config_source}")
    logger.info(f"ChromaDB path: {settings.CHROMA_DB_PATH}")
    logger.info(f"Using embedding model: {settings.EMBEDDING_MODEL}")
    
    # Verify OpenAI API key is set
    if not settings.OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY is not set! The application may not function correctly.")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.ENV == "development",
    )
