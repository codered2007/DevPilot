from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    owner: str
    repo: str
    message: str
    history: list[ChatMessage] = []