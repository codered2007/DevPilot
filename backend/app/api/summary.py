from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_session
from app.api.repositories import get_accessible_repository
from app.services.repository_summary import summarize_repository


router = APIRouter(
    prefix="/summary",
    tags=["Summary"],
)


@router.get("/")
async def repository_summary(
    owner: str,
    repo: str,
    session: dict = Depends(get_current_session),
):
    await get_accessible_repository(
        owner,
        repo,
        session["access_token"],
    )

    summary = await summarize_repository(
        owner,
        repo,
        token=session["access_token"],
    )

    return {
        "summary": summary,
    }