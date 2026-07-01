from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    user_id: str = Field(default="default")
    session_id: str = Field(default="default")
    message: str = Field()

class ChatResponse(BaseModel):
    answer: str = Field()
