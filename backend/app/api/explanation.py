
from fastapi import APIRouter, Depends, HTTPException, Query

from app import database
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
    workspace_id: str = Query(..., min_length=1),
    session: dict = Depends(get_current_session),
):
    token = session.get("access_token")
    if not token:
        raise HTTPException(
            status_code=401,
            detail="GitHub authentication required",
        )

    await get_accessible_repository(
        request.owner,
        request.repo,
        token,
    )

    user_id = session["github_user"]["id"]

    activity = database.create_activity(
        user_id=user_id,
        workspace_id=workspace_id,
        owner=request.owner,
        repo=request.repo,
        action_type="code_explanation",
        title=f"Explain code in {request.file_path}",
        details={
            "file_path": request.file_path,
        },
    )

    try:
        response = await explain_code(
            request.owner,
            request.repo,
            request.file_path,
            request.code,
        )

        if not response:
            raise HTTPException(
                status_code=400,
                detail="Code explanation could not be generated",
            )

        database.complete_activity(
            activity_id=activity["id"],
            user_id=user_id,
            workspace_id=workspace_id,
            status="success",
            details={
                "explanation": response,
            },
        )

        return {
            "response": response,
        }

    except Exception as exc:
        database.complete_activity(
            activity_id=activity["id"],
            user_id=user_id,
            workspace_id=workspace_id,
            status="failed",
            details={
                "error_type": type(exc).__name__,
            },
        )
        raise
