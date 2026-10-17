
from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_current_session
from app.api.repositories import get_accessible_repository
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

    dependencies = await analyze_repository_dependencies(
        owner,
        repo,
        token=token,
    )

    if not dependencies:
        raise HTTPException(
            status_code=400,
            detail="Unable to analyze repository dependencies.",
        )

    result = await analyze_repository_security(
        dependencies.get("dependencies", [])
    )

    return result
