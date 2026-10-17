from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_session
from app.api.repositories import get_accessible_repository
from app.services.repository_indexer import index_repository


router = APIRouter(
    prefix="/index",
    tags=["Index"],
)


@router.post("/")
async def index(
    owner: str,
    repo: str,
    session: dict = Depends(get_current_session),
):
    await get_accessible_repository(
        owner,
        repo,
        session["access_token"],
    )

    result = await index_repository(
        owner,
        repo,
        token=session["access_token"],
        user_id=session["github_user"]["id"],
    )

    return result