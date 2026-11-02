
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    owner: str
    repo: str
    message: str
    conversation_id: str | None = None
    history: list[ChatMessage] = Field(default_factory=list)
