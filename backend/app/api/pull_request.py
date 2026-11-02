
import httpx
from fastapi import APIRouter, Depends, HTTPException

from app import database
from app.api.dependencies import get_current_session
from app.api.repositories import (
    get_accessible_repository,
    _raise_github_http_error,
    _raise_github_network_error,
)
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
            owner=request.owner,
            repo=request.repo,
            action_type="pull_request",
            title=f"Create pull request: {request.title}",
            details={
                "title": request.title,
                "head": request.head,
                "base": request.base,
            },
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

        if not result:
            raise HTTPException(
                status_code=400,
                detail="Unable to create Pull Request on GitHub.",
            )

        if activity:
            database.complete_activity(
                activity_id=activity["id"],
                user_id=user_id,
                status="success",
                details={
                    "number": result["number"],
                    "title": result["title"],
                    "url": result["url"],
                    "state": result["state"],
                    "head": result["head"],
                    "base": result["base"],
                },
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

    except HTTPException:
        if activity:
            database.complete_activity(
                activity_id=activity["id"],
                user_id=user_id,
                status="failed",
                details={"error_type": "HTTPException"},
            )
        raise

    except httpx.HTTPStatusError as error:
        if activity:
            database.complete_activity(
                activity_id=activity["id"],
                user_id=user_id,
                status="failed",
                details={"error_type": type(error).__name__},
            )

        _raise_github_http_error(
            error,
            operation="pull request creation",
        )

    except httpx.RequestError as error:
        if activity:
            database.complete_activity(
                activity_id=activity["id"],
                user_id=user_id,
                status="failed",
                details={"error_type": type(error).__name__},
            )

        _raise_github_network_error(
            error,
            operation="pull request creation",
        )

    except Exception as exc:
        if activity:
            database.complete_activity(
                activity_id=activity["id"],
                user_id=user_id,
                status="failed",
                details={"error_type": type(exc).__name__},
            )
        raise
