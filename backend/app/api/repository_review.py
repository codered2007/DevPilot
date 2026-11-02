
from fastapi import APIRouter, Depends, HTTPException

from app import database
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

    user_id = session["github_user"]["id"]

    activity = database.create_activity(
        user_id=user_id,
        owner=owner,
        repo=repo,
        action_type="repository_review",
        title=f"Review repository {owner}/{repo}",
    )

    try:
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

        database.complete_activity(
            activity_id=activity["id"],
            user_id=user_id,
            status="success",
            details={
                "review": result,
            },
        )

        return result

    except Exception as exc:
        database.complete_activity(
            activity_id=activity["id"],
            user_id=user_id,
            status="failed",
            details={
                "error_type": type(exc).__name__,
            },
        )
        raise
