from fastapi import APIRouter, HTTPException

from app.schemas.pull_request import CreatePullRequestRequest

from app.services.github_service import (
    create_pull_request,
)


router = APIRouter(
    prefix="/pull-request",
    tags=["Pull Request"],
)


@router.post("/")
async def create_pull_request_route(
    request: CreatePullRequestRequest,
):
    result = await create_pull_request(
        request.owner,
        request.repo,
        request.title,
        request.body,
        request.head,
        request.base,
    )

    if not result:
        raise HTTPException(
            status_code=400,
            detail="Unable to create Pull Request on GitHub.",
        )

    return {
        "message": "Pull Request created successfully.",
        "owner": request.owner,
        "repo": request.repo,
        "number": result["number"],
        "title": result["title"],
        "url": result["url"],
        "state": result["state"],
        "head": result["head"],
        "base": result["base"],
    }