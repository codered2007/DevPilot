
from fastapi import APIRouter, Depends, Query

from app import database
from app.api.dependencies import get_current_session
from app.api.repositories import get_accessible_repository
from app.services.repository_indexer import index_repository


router = APIRouter(
    prefix="/index",
    tags=["Index"],
)


@router.post("/")
async def index(
    owner: str,
    repo: str,
    workspace_id: str = Query(..., min_length=1),
    session: dict = Depends(get_current_session),
):
    await get_accessible_repository(
        owner,
        repo,
        session["access_token"],
    )

    user_id = session["github_user"]["id"]

    activity = database.create_activity(
        user_id=user_id,
        workspace_id=workspace_id,
        owner=owner,
        repo=repo,
        action_type="index",
        title=f"Index repository {owner}/{repo}",
    )

    try:
        result = await index_repository(
            owner,
            repo,
            token=session["access_token"],
            user_id=user_id,
        )

        database.complete_activity(
            activity_id=activity["id"],
            user_id=user_id,
            workspace_id=workspace_id,
            status="success",
            details={
                "indexed_files": result["indexed_files"],
                "indexed_chunks": result["indexed_chunks"],
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
