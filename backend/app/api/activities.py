
from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import get_current_session
from app import database


router = APIRouter(
    prefix="/activities",
    tags=["Activity History"],
)


def get_user_id(session: dict) -> int:
    github_user = session.get("github_user", {})
    user_id = (
        github_user.get("id")
        if isinstance(github_user, dict)
        else None
    )

    if not isinstance(user_id, int) or isinstance(user_id, bool):
        raise HTTPException(
            status_code=401,
            detail="Invalid authenticated user.",
        )

    return user_id


@router.get("/")
async def list_user_activities(
    workspace_id: str = Query(..., min_length=1),
    owner: str | None = None,
    repo: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    session: dict = Depends(get_current_session),
):
    user_id = get_user_id(session)
    workspace_id = workspace_id.strip()

    if (owner is None) != (repo is None):
        raise HTTPException(
            status_code=400,
            detail="Both owner and repo must be provided together.",
        )

    try:
        activities = database.list_activities(
            user_id=user_id,
            workspace_id=workspace_id,
            owner=owner,
            repo=repo,
            limit=limit,
        )
    except ValueError:
        raise HTTPException(
            status_code=404,
            detail="Workspace not found.",
        ) from None

    return {
        "activities": activities,
        "count": len(activities),
    }


@router.get("/{activity_id}")
async def get_user_activity(
    activity_id: str,
    workspace_id: str = Query(..., min_length=1),
    session: dict = Depends(get_current_session),
):
    user_id = get_user_id(session)

    activity = database.get_activity(
        activity_id=activity_id,
        user_id=user_id,
        workspace_id=workspace_id.strip(),
    )

    if activity is None:
        raise HTTPException(
            status_code=404,
            detail="Activity not found.",
        )

    return {"activity": activity}
