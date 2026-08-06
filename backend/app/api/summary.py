from fastapi import APIRouter

from app.services.repository_summary import summarize_repository

router = APIRouter(
    prefix="/summary",
    tags=["Summary"],
)


@router.get("/")
async def repository_summary(
    owner: str,
    repo: str,
):
    summary = await summarize_repository(
        owner,
        repo,
    )

    return {
        "summary": summary,
    }