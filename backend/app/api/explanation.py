from fastapi import APIRouter, HTTPException, status

from app.schemas.explanation import ExplainRequest
from app.services.explanation_service import explain_code

router = APIRouter(
    prefix="/explain",
    tags=["Explanation"],
)


@router.post("/", status_code=status.HTTP_200_OK)
async def explain(request: ExplainRequest):
    try:
        response = await explain_code(
            owner=request.owner,
            repo=request.repo,
            file_path=request.file_path,
            code=request.code,
        )
        if not response:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Empty response received from explanation service.",
            )
        return {"response": response}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate explanation: {str(e)}",
        )