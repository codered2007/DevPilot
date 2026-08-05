from pydantic import BaseModel


class ChatRequest(BaseModel):
    owner: str
    repo: str
    message: str