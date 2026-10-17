
import re
import uuid

import httpx
from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_current_session
from app.api.repositories import get_accessible_repository
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
):
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

    # Verify authenticated user access before any write operation.
    await get_accessible_repository(
        request.owner,
        request.repo,
        token,
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
        raise

    except httpx.HTTPStatusError as error:
        status_code = error.response.status_code

        if status_code == 401:
            raise HTTPException(
                status_code=401,
                detail=(
                    "GitHub authentication failed. "
                    "Please sign in again."
                ),
            ) from error

        if status_code == 403:
            raise HTTPException(
                status_code=403,
                detail="Access to this repository is forbidden.",
            ) from error

        if status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="Repository resource not found or access denied.",
            ) from error

        raise HTTPException(
            status_code=502,
            detail=(
                "GitHub returned an unexpected error "
                "during code application."
            ),
        ) from error

    except httpx.RequestError as error:
        raise HTTPException(
            status_code=502,
            detail=(
                "Unable to communicate with GitHub "
                "during code application."
            ),
        ) from error
