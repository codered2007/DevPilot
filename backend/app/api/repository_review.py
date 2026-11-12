
from fastapi import APIRouter, Depends, HTTPException, Query

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
    workspace_id: str = Query(..., min_length=1),
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
        workspace_id=workspace_id,
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
                status_code=502,
                detail="The AI provider returned an empty or invalid review response.",
            )

        database.complete_activity(
            activity_id=activity["id"],
            user_id=user_id,
            workspace_id=workspace_id,
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
            workspace_id=workspace_id,
            status="failed",
            details={
                "error_type": type(exc).__name__,
                "error": str(exc),
            },
        )

        if isinstance(exc, HTTPException):
            raise

        error_message = str(exc).lower()

        if "currently unavailable" in error_message:
            raise HTTPException(
                status_code=503,
                detail="AI service is temporarily unavailable. Please try again later.",
            ) from exc

        raise HTTPException(
            status_code=502,
            detail="Repository review failed because an upstream service returned an error.",
        ) from exc
