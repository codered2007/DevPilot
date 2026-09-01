from fastapi import APIRouter

from app.schemas.explanation import ExplainRequest
from app.services.explanation_service import explain_code


router = APIRouter(
    prefix="/explain",
    tags=["Explanation"],
)


@router.post("/")
async def explain(
    request: ExplainRequest,
):
    response = await explain_code(
        request.owner,
        request.repo,
        request.file_path,
        request.code,
    )

    return {
        "response": response,
    }