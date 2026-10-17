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
    Verify that the logged-in user's GitHub token can access
    the requested repository.
    """
    try:
        repository = await get_repository(
            owner,
            repo,
            token=token,
        )

    except httpx.HTTPStatusError as error:
        status_code = error.response.status_code

        print(f"GitHub API error: HTTP {status_code}")
        print(f"GitHub response: {error.response.text}")

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
                detail="Repository not found or access denied.",
            ) from error

        raise HTTPException(
            status_code=502,
            detail=f"GitHub API returned HTTP {status_code}.",
        ) from error

    except httpx.RequestError as error:
        print(
            f"GitHub network error: "
            f"{type(error).__name__}: {error}"
        )

        raise HTTPException(
            status_code=502,
            detail="Unable to communicate with GitHub.",
        ) from error

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
    try:
        return await get_repository_tree(
            owner,
            repo,
            token=token,
        )

    except httpx.HTTPStatusError as error:
        print(
            "GitHub tree API error: "
            f"HTTP {error.response.status_code}"
        )
        print(f"GitHub response: {error.response.text}")

        raise HTTPException(
            status_code=502,
            detail=(
                "GitHub returned an unexpected error "
                "while fetching the repository tree."
            ),
        ) from error

    except httpx.RequestError as error:
        print(
            f"GitHub tree network error: "
            f"{type(error).__name__}: {error}"
        )

        raise HTTPException(
            status_code=502,
            detail=(
                "Unable to communicate with GitHub "
                "while fetching the repository tree."
            ),
        ) from error


@router.post("/import")
async def import_repository(
    request: RepositoryImportRequest,
    session: dict = Depends(get_current_session),
):
    parts = request.url.rstrip("/").split("/")

    if len(parts) < 5:
        raise HTTPException(
            status_code=400,
            detail="Invalid GitHub URL",
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
        print(
            "GitHub file API error: "
            f"HTTP {error.response.status_code}"
        )
        print(f"GitHub response: {error.response.text}")

        raise HTTPException(
            status_code=502,
            detail=(
                "GitHub returned an unexpected error "
                "while fetching the file."
            ),
        ) from error

    except httpx.RequestError as error:
        print(
            f"GitHub file network error: "
            f"{type(error).__name__}: {error}"
        )

        raise HTTPException(
            status_code=502,
            detail=(
                "Unable to communicate with GitHub "
                "while fetching the file."
            ),
        ) from error

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
        print(
            "GitHub search API error: "
            f"HTTP {error.response.status_code}"
        )
        print(f"GitHub response: {error.response.text}")

        raise HTTPException(
            status_code=502,
            detail=(
                "GitHub returned an error "
                "while searching the repository."
            ),
        ) from error

    except httpx.RequestError as error:
        print(
            f"GitHub search network error: "
            f"{type(error).__name__}: {error}"
        )

        raise HTTPException(
            status_code=502,
            detail=(
                "Unable to communicate with GitHub "
                "while searching."
            ),
        ) from error