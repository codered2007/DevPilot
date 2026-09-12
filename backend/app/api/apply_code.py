import re
import uuid

from fastapi import APIRouter, HTTPException

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
):
    default_branch = await get_default_branch(
        request.owner,
        request.repo,
    )

    if not default_branch:
        raise HTTPException(
            status_code=404,
            detail=(
                "Unable to determine "
                "repository default branch."
            ),
        )

    base_sha = await get_branch_sha(
        request.owner,
        request.repo,
        default_branch,
    )

    if not base_sha:
        raise HTTPException(
            status_code=404,
            detail=(
                "Unable to determine "
                "base branch commit."
            ),
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
    )

    if not branch_ref:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unable to create GitHub branch."
            ),
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
    )

    if not result:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unable to update "
                "file on GitHub."
            ),
        )

    return {
        "message": (
            "Code applied successfully."
        ),
        "owner": request.owner,
        "repo": request.repo,
        "file_path": request.file_path,
        "action": request.action,
        "branch": result["branch"],
        "commit_sha": result["commit_sha"],
        "commit_url": result["commit_url"],
    }