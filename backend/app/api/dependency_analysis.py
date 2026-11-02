
from fastapi import APIRouter, Depends, HTTPException

from app import database
from app.api.dependencies import get_current_session
from app.api.repositories import get_accessible_repository
from app.services.dependency_analysis import (
    analyze_repository_dependencies,
)


router = APIRouter(
    prefix="/dependency-analysis",
    tags=["Dependency Analysis"],
)


@router.post("/")
async def dependency_analysis(
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
        action_type="dependency_analysis",
        title=f"Analyze dependencies of {owner}/{repo}",
    )

    try:
        result = await analyze_repository_dependencies(
            owner,
            repo,
            token=token,
        )

        if not result:
            raise HTTPException(
                status_code=400,
                detail="Unable to analyze repository dependencies.",
            )

        database.complete_activity(
            activity_id=activity["id"],
            user_id=user_id,
            status="success",
            details={
                "dependency_analysis": result,
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
