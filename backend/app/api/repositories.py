from fastapi import APIRouter, HTTPException

from app.schemas.repository import RepositoryImportRequest
from app.services.github_service import (
    get_repository,
    get_repository_tree,
    get_file_content,
)

router = APIRouter(
    prefix="/repositories",
    tags=["Repositories"],
)


@router.get("/")
def list_repositories():
    return {
        "message": "Repository API is working!"
    }


@router.post("/import")
async def import_repository(
    request: RepositoryImportRequest,
):
    parts = request.url.rstrip("/").split("/")

    if len(parts) < 5:
        raise HTTPException(
            status_code=400,
            detail="Invalid GitHub URL",
        )

    owner = parts[-2]
    repo = parts[-1]

    repository = await get_repository(owner, repo)

    if repository is None:
        raise HTTPException(
            status_code=404,
            detail="Repository not found",
        )

    return {
        "owner": owner,
        "repo": repo,
        "name": repository["full_name"],
        "description": repository["description"],
        "stars": repository["stargazers_count"],
        "forks": repository["forks_count"],
        "language": repository["language"],
        "branch": repository["default_branch"],
    }


@router.get("/tree")
async def repository_tree(
    owner: str,
    repo: str,
):
    tree = await get_repository_tree(owner, repo)

    if tree is None:
        raise HTTPException(
            status_code=404,
            detail="Repository tree not found",
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
):
    file = await get_file_content(owner, repo, path)

    if file is None:
        raise HTTPException(
            status_code=404,
            detail="File not found",
        )

    return file