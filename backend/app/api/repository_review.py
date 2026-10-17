
from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_current_session
from app.api.repositories import get_accessible_repository
from app.services.repository_review import review_repository


router = APIRouter(
    prefix="/repository-review",
    tags=["Repository Review"],
)


@router.post("/")
async def repository_review(
    owner: str,
    repo: str,
    session: dict = Depends(get_current_session),
):
    token = session.get("access_token")

    if not token:
        raise HTTPException(
            status_code=401,
            detail=(
                "GitHub access token is missing. "
                "Please sign in again."
            ),
        )

    await get_accessible_repository(
        owner,
        repo,
        token,
    )

    result = await review_repository(
        owner,
        repo,
        token=token,
    )

    if not result:
        raise HTTPException(
            status_code=400,
            detail="Unable to review repository.",
        )

    return result
