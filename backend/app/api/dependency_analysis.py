from fastapi import APIRouter, HTTPException

from app.services.dependency_analysis import (
    analyze_repository_dependencies,
)


router = APIRouter(
    prefix="/dependency-analysis",
    tags=["Dependency Analysis"],
)


@router.post("/")
async def dependency_analysis(
    owner: str,
    repo: str,
):
    result = await analyze_repository_dependencies(
        owner,
        repo,
    )

    if not result:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unable to analyze repository dependencies."
            ),
        )

    return result