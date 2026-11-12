
import re
import uuid

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query

from app import database
from app.api.dependencies import get_current_session
from app.api.repositories import (
    get_accessible_repository,
    _raise_github_http_error,
    _raise_github_network_error,
)
from app.schemas.apply_code import ApplyCodeRequest
from app.services.github_service import (
    get_default_branch,
    get_branch_sha,
    create_branch,
    update_file_on_branch,
)

router = APIRouter(
    prefix="/apply-code",
    tags=["Apply Code"],
)


def create_branch_name(
    file_path: str,
    action: str,
) -> str:
    filename = file_path.split("/")[-1]

    filename = re.sub(
        r"[^a-zA-Z0-9._-]",
        "-",
        filename,
    )

    unique_id = uuid.uuid4().hex[:8]

    return (
        f"devpilot/"
        f"{action}-"
        f"{filename}-"
        f"{unique_id}"
    )


@router.post("/")
async def apply_code(
    request: ApplyCodeRequest,
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
        request.owner,
        request.repo,
        token,
    )

    github_user = session.get("github_user")
    user_id = github_user.get("id") if isinstance(github_user, dict) else None

    activity = None

    if isinstance(user_id, int) and not isinstance(user_id, bool):
        activity = database.create_activity(
            user_id=user_id,
            workspace_id=workspace_id,
            owner=request.owner,
            repo=request.repo,
            action_type="apply_code",
            title=f"Apply {request.action} to {request.file_path}",
            details={
                "file_path": request.file_path,
                "action": request.action,
            },
        )

    try:
        default_branch = await get_default_branch(
            request.owner,
            request.repo,
            token=token,
        )

        if not default_branch:
            raise HTTPException(
                status_code=404,
                detail="Unable to determine repository default branch.",
            )

        base_sha = await get_branch_sha(
            request.owner,
            request.repo,
            default_branch,
            token=token,
        )

        if not base_sha:
            raise HTTPException(
                status_code=404,
                detail="Unable to determine base branch commit.",
            )

        branch = create_branch_name(
            request.file_path,
            request.action,
        )

        branch_ref = await create_branch(
            request.owner,
            request.repo,
            branch,
            base_sha,
            token=token,
        )

        if not branch_ref:
            raise HTTPException(
                status_code=400,
                detail="Unable to create GitHub branch.",
            )

        commit_message = (
            f"devpilot: "
            f"{request.action} "
            f"{request.file_path}"
        )

        result = await update_file_on_branch(
            request.owner,
            request.repo,
            request.file_path,
            request.code,
            branch,
            commit_message,
            token=token,
        )

        if not result:
            raise HTTPException(
                status_code=400,
                detail="Unable to update file on GitHub.",
            )

        if activity:
            database.complete_activity(
                activity_id=activity["id"],
                user_id=user_id,
                workspace_id=workspace_id,
                status="success",
                details={
                    "file_path": request.file_path,
                    "action": request.action,
                    "branch": result["branch"],
                    "base_branch": default_branch,
                    "commit_sha": result["commit_sha"],
                    "commit_url": result["commit_url"],
                },
            )

        return {
            "message": "Code applied successfully.",
            "owner": request.owner,
            "repo": request.repo,
            "file_path": request.file_path,
            "action": request.action,
            "branch": result["branch"],
            "base_branch": default_branch,
            "commit_sha": result["commit_sha"],
            "commit_url": result["commit_url"],
        }

    except HTTPException:
        if activity:
            database.complete_activity(
                activity_id=activity["id"],
                user_id=user_id,
                workspace_id=workspace_id,
                status="failed",
                details={"error_type": "HTTPException"},
            )
        raise

    except httpx.HTTPStatusError as error:
        if activity:
            database.complete_activity(
                activity_id=activity["id"],
                user_id=user_id,
                workspace_id=workspace_id,
                status="failed",
                details={"error_type": type(error).__name__},
            )

        _raise_github_http_error(
            error,
            operation="code application",
        )

    except httpx.RequestError as error:
        if activity:
            database.complete_activity(
                activity_id=activity["id"],
                user_id=user_id,
                workspace_id=workspace_id,
                status="failed",
                details={"error_type": type(error).__name__},
            )

        _raise_github_network_error(
            error,
            operation="code application",
        )

    except Exception as exc:
        if activity:
            database.complete_activity(
                activity_id=activity["id"],
                user_id=user_id,
                workspace_id=workspace_id,
                status="failed",
                details={"error_type": type(exc).__name__},
            )
        raise
