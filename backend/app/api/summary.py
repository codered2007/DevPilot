
from fastapi import APIRouter, Depends, HTTPException

from app import database
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
        action_type="repository_summary",
        title=f"Summarize repository {owner}/{repo}",
    )

    try:
        summary = await summarize_repository(
            owner,
            repo,
            token=token,
        )

        if not summary:
            raise HTTPException(
                status_code=400,
                detail="Unable to summarize repository.",
            )

        database.complete_activity(
            activity_id=activity["id"],
            user_id=user_id,
            status="success",
            details={
                "summary": summary,
            },
        )

        return {
            "summary": summary,
        }

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
