
from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_current_session
from app.schemas.pull_request import CreatePullRequestRequest
from app.services.github_service import create_pull_request


router = APIRouter(
    prefix="/pull-request",
    tags=["Pull Request"],
)


@router.post("/")
async def create_pull_request_route(
    request: CreatePullRequestRequest,
    session: dict = Depends(get_current_session),
):
    token = session["access_token"]

    result = await create_pull_request(
        request.owner,
        request.repo,
        request.title,
        request.body,
        request.head,
        request.base,
        token=token,
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
