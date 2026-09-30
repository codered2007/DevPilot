from fastapi import APIRouter, HTTPException

from app.services.dependency_analysis import (
    analyze_repository_dependencies,
)
from app.services.security_analysis import (
    analyze_repository_security,
)


router = APIRouter(
    prefix="/security-analysis",
    tags=["Security Analysis"],
)


@router.post("/")
async def security_analysis(
    owner: str,
    repo: str,
):
    dependencies = (
        await analyze_repository_dependencies(
            owner,
            repo,
        )
    )

    if not dependencies:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unable to analyze repository "
                "dependencies."
            ),
        )

    result = await analyze_repository_security(
        dependencies.get(
            "dependencies",
            [],
        )
    )

    return result