# Standard imports
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers import chat_router, save_chat_router

logger = logging.getLogger("uvicorn")

app = FastAPI(
    title="Conversational Resume Chatbot",
    description="A chatbot that can answer questions about my resume and portfolio",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat_router, prefix="/api")
app.include_router(save_chat_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Welcome to the Conversational Resume Chatbot API"}

@app.get("/ping")
async def ping():
    return {"message": "pong"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Completed request: {request.method} {request.url} with status {response.status_code}")
    return response
