
from fastapi import APIRouter, Depends, HTTPException, Query

from app import database
from app.api.dependencies import get_current_session
from app.api.repositories import get_accessible_repository
from app.services.architecture_analysis import (
    analyze_repository_architecture,
)


router = APIRouter(
    prefix="/architecture-analysis",
    tags=["Architecture Analysis"],
)


@router.post("/")
async def architecture_analysis(
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
        action_type="architecture_analysis",
        title=f"Analyze architecture of {owner}/{repo}",
    )

    try:
        result = await analyze_repository_architecture(
            owner,
            repo,
            token=token,
        )

        if not result:
            raise HTTPException(
                status_code=400,
                detail="Unable to analyze repository architecture.",
            )

        database.complete_activity(
            activity_id=activity["id"],
            user_id=user_id,
            workspace_id=workspace_id,
            status="success",
            details={
                "architecture_analysis": result,
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
            },
        )
        raise
