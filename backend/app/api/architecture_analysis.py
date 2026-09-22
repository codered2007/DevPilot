from fastapi import APIRouter, HTTPException

from app.services.architecture_analysis import (
    analyze_repository_architecture,
)


router = APIRouter(
    prefix="/architecture-analysis",
    tags=["Architecture Analysis"],
)


@router.post("/")
async def architecture_analysis(
    owner: str,
    repo: str,
):
    result = await analyze_repository_architecture(
        owner,
        repo,
    )

    if not result:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unable to analyze repository architecture."
            ),
        )

    return result