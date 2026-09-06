from fastapi import APIRouter

from app.schemas.chat import ChatRequest
from app.services.ai_service import ask_ai

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post("/")
async def chat(
    request: ChatRequest,
):
    response = await ask_ai(
        request.owner,
        request.repo,
        request.message,
    )

    return response