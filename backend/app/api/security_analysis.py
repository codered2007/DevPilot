
from fastapi import APIRouter, Depends, HTTPException, Query

from app import database
from app.api.dependencies import get_current_session
from app.api.repositories import get_accessible_repository
from app.services.dependency_analysis import (
    analyze_repository_dependencies,
)
from app.services.security_analysis import (
    analyze_repository_security,
)


router = APIRouter(
    prefix="/security-analysis",
    tags=["Security Analysis"],
)


@router.post("/")
async def security_analysis(
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
        action_type="security_analysis",
        title=f"Analyze security of {owner}/{repo}",
    )

    try:
        dependencies = await analyze_repository_dependencies(
            owner,
            repo,
            token=token,
        )

        if not dependencies:
            raise HTTPException(
                status_code=400,
                detail="Unable to analyze repository dependencies.",
            )

        result = await analyze_repository_security(
            dependencies.get("dependencies", [])
        )

        if not result:
            raise HTTPException(
                status_code=400,
                detail="Unable to analyze repository security.",
            )

        database.complete_activity(
            activity_id=activity["id"],
            user_id=user_id,
            workspace_id=workspace_id,
            status="success",
            details={
                "security_analysis": result,
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
