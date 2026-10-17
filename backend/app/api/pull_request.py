
import httpx
from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_current_session
from app.api.repositories import get_accessible_repository
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
    token = session.get("access_token")

    if not token:
        raise HTTPException(
            status_code=401,
            detail=(
                "GitHub access token is missing. "
                "Please sign in again."
            ),
        )

    # Verify repository access before creating a pull request.
    await get_accessible_repository(
        request.owner,
        request.repo,
        token,
    )

    try:
        result = await create_pull_request(
            request.owner,
            request.repo,
            request.title,
            request.body,
            request.head,
            request.base,
            token=token,
        )

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
                detail=(
                    "You are not authorized to create "
                    "a pull request."
                ),
            ) from error

        if status_code == 404:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Repository or pull request branch "
                    "not found."
                ),
            ) from error

        raise HTTPException(
            status_code=502,
            detail=(
                "GitHub returned an unexpected error "
                "while creating the pull request."
            ),
        ) from error

    except httpx.RequestError as error:
        raise HTTPException(
            status_code=502,
            detail=(
                "Unable to communicate with GitHub "
                "while creating the pull request."
            ),
        ) from error

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
