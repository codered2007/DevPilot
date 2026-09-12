from fastapi import APIRouter, HTTPException, status

from app.schemas.explanation import ExplainRequest
from app.services.explanation_service import explain_code


router = APIRouter(
    prefix="/explain",
    tags=["Explanation"],
)


@router.post("/", status_code=status.HTTP_200_OK)
async def explain(
    request: ExplainRequest,
):
    try:
        response = await explain_code(
            request.owner,
            request.repo,
            request.file_path,
            request.code,
        )
        return {
            "response": response,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while generating the explanation: {exc}",
        )