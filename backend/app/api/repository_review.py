from fastapi import APIRouter, HTTPException

from app.services.repository_review import review_repository


router = APIRouter(
    prefix="/repository-review",
    tags=["Repository Review"],
)


@router.post("/")
async def repository_review(
    owner: str,
    repo: str,
):
    result = await review_repository(
        owner,
        repo,
    )

    if not result:
        raise HTTPException(
            status_code=400,
            detail="Unable to review repository.",
        )

    return result