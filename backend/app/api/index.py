from fastapi import APIRouter

from app.services.repository_indexer import (
    index_repository,
)


router = APIRouter(
    prefix="/index",
    tags=["Index"],
)


@router.post("/")
async def index(
    owner: str,
    repo: str,
):
    result = await index_repository(
        owner,
        repo,
    )

    return result