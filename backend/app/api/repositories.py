import httpx
from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_current_session
from app.schemas.repository import RepositoryImportRequest
from app.services.github_service import (
    get_repository,
    get_repository_tree,
    get_file_content,
    search_repository,
)

router = APIRouter(
    prefix="/repositories",
    tags=["Repositories"],
)


def _raise_github_http_error(
    error: httpx.HTTPStatusError,
    operation: str = "accessing the repository",
) -> None:
    """Translate GitHub API errors into safe, consistent HTTP responses."""
    response = error.response
    status_code = response.status_code

    try:
        response_body = response.json()
        message = (
            response_body.get("message", "")
            if isinstance(response_body, dict)
            else ""
        )
    except (ValueError, TypeError):
        message = ""

    message = message.lower()
    retry_after = response.headers.get("Retry-After")


    is_rate_limited = (
        status_code == 429
        or (
            status_code == 403
            and (
                response.headers.get("X-RateLimit-Remaining") == "0"
                or bool(retry_after)
                or "rate limit" in message
                or "secondary rate" in message
            )
        )
    )

    if is_rate_limited:
        headers = {}

        if retry_after:
            headers["Retry-After"] = retry_after

        raise HTTPException(
            status_code=429,
            detail="GitHub API rate limit reached. Please retry later.",
            headers=headers,
        ) from error

    if status_code == 401:
        raise HTTPException(
            status_code=401,
            detail=(
                "GitHub authentication failed. "
                "Please reconnect your GitHub account."
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
        detail=f"GitHub returned an unexpected error while {operation}.",
    ) from error


def _raise_github_network_error(
    error: httpx.RequestError,
    operation: str = "accessing the repository",
) -> None:
    """Return a safe error without exposing request details."""
    raise HTTPException(
        status_code=502,
        detail=f"Unable to communicate with GitHub while {operation}.",
    ) from error


@router.get("/")
def list_repositories(
    session: dict = Depends(get_current_session),
):
    return {
        "message": "Repository API is working!"
    }


async def get_accessible_repository(
    owner: str,
    repo: str,
    token: str,
):
    """
    Verify that the authenticated user's GitHub token can access
    the requested repository.
    """
    if not token:
        raise HTTPException(
            status_code=401,
            detail="GitHub access token is missing. Please sign in again.",
        )

    try:
        repository = await get_repository(
            owner,
            repo,
            token=token,
        )

    except httpx.HTTPStatusError as error:
        _raise_github_http_error(
            error,
            operation="accessing the repository",
        )

    except httpx.RequestError as error:
        _raise_github_network_error(
            error,
            operation="accessing the repository",
        )

    if repository is None:
        raise HTTPException(
            status_code=404,
            detail="Repository not found or access denied.",
        )

    return repository


async def get_repository_tree_safely(
    owner: str,
    repo: str,
    token: str,
):
    """Fetch the repository tree and translate GitHub errors safely."""
    try:
        return await get_repository_tree(
            owner,
            repo,
            token=token,
        )

    except httpx.HTTPStatusError as error:
        _raise_github_http_error(
            error,
            operation="fetching the repository tree",
        )

    except httpx.RequestError as error:
        _raise_github_network_error(
            error,
            operation="fetching the repository tree",
        )


@router.post("/import")
async def import_repository(
    request: RepositoryImportRequest,
    session: dict = Depends(get_current_session),
):
    parts = request.url.rstrip("/").split("/")

    if len(parts) < 5:
        raise HTTPException(
            status_code=400,
            detail="Invalid GitHub URL.",
        )

    owner = parts[-2]
    repo = parts[-1]
    token = session.get("access_token")

    if not token:
        raise HTTPException(
            status_code=401,
            detail=(
                "GitHub access token is missing. "
                "Please sign in again."
            ),
        )

    repository = await get_accessible_repository(
        owner,
        repo,
        token,
    )

    return {
        "owner": owner,
        "repo": repo,
        "name": repository["full_name"],
        "description": repository.get("description") or "",
        "stars": repository["stargazers_count"],
        "forks": repository["forks_count"],
        "language": repository.get("language") or "",
        "branch": repository["default_branch"],
    }


@router.get("/tree")
async def repository_tree(
    owner: str,
    repo: str,
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

    tree = await get_repository_tree_safely(
        owner,
        repo,
        token,
    )

    if tree is None:
        raise HTTPException(
            status_code=404,
            detail="Repository tree not found.",
        )

    return [
        {
            "path": item["path"],
            "type": item["type"],
        }
        for item in tree["tree"]
    ]


@router.get("/file")
async def repository_file(
    owner: str,
    repo: str,
    path: str,
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

    try:
        file = await get_file_content(
            owner,
            repo,
            path,
            token=token,
        )

    except httpx.HTTPStatusError as error:
        _raise_github_http_error(
            error,
            operation="fetching the file",
        )

    except httpx.RequestError as error:
        _raise_github_network_error(
            error,
            operation="fetching the file",
        )

    if file is None:
        raise HTTPException(
            status_code=404,
            detail="File not found or access denied.",
        )

    return file


@router.get("/search")
async def repository_search(
    owner: str,
    repo: str,
    query: str,
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

    try:
        return await search_repository(
            owner,
            repo,
            query,
            token=token,
        )

    except httpx.HTTPStatusError as error:
        _raise_github_http_error(
            error,
            operation="searching the repository",
        )

    except httpx.RequestError as error:
        _raise_github_network_error(
            error,
            operation="searching the repository",
        )
