from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_session
from app.api.repositories import get_accessible_repository
from app.schemas.chat import ChatRequest
from app.services.ai_service import ask_ai


router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post("/")
async def chat(
    request: ChatRequest,
    session: dict = Depends(get_current_session),
):
    await get_accessible_repository(
        request.owner,
        request.repo,
        session["access_token"],
    )

    response = await ask_ai(
        request.owner,
        request.repo,
        request.message,
        request.history,
        user_id=session["github_user"]["id"],
    )

    return response