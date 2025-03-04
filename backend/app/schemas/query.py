from pydantic import BaseModel, EmailStr
from typing import Optional, Dict

class UserInfo(BaseModel):
    name: str
    email: EmailStr
    companyName: str
    companyType: str
    purpose: str
    jobRole: str
    sessionId: str
    
    model_config = {"from_attributes": True}

class ChatQuery(BaseModel):
    query: str
    user_info: UserInfo
    session_id: str
    
    model_config = {"from_attributes": True}

class SaveChatQuery(BaseModel):
    session_id: str
    user_info: UserInfo
    messages: list[Dict]
    
    model_config = {"from_attributes": True}

# Frontend request DTO that matches the actual format sent by the client
class ChatRequestDto(BaseModel):
    query: str
    language: str
    thread_id: str
    
    model_config = {"from_attributes": True}
