from pydantic import BaseModel

class ChatResponse(BaseModel):
    response: str

    model_config = {"from_attributes": True}
