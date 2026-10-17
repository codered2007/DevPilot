from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_session
from app.api.repositories import get_accessible_repository
from app.schemas.explanation import ExplainRequest
from app.services.explanation_service import explain_code


router = APIRouter(
    prefix="/explain",
    tags=["Explanation"],
)


@router.post("/")
async def explain(
    request: ExplainRequest,
    session: dict = Depends(get_current_session),
):
    await get_accessible_repository(
        request.owner,
        request.repo,
        session["access_token"],
    )

    response = await explain_code(
        request.owner,
        request.repo,
        request.file_path,
        request.code,
    )

    return {
        "response": response,
    }