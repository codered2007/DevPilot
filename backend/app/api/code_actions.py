
from fastapi import APIRouter, Depends, HTTPException, Query

from app import database
from app.api.dependencies import get_current_session
from app.api.repositories import get_accessible_repository
from app.schemas.code_actions import CodeActionRequest
from app.services.code_action_service import generate_code_action


router = APIRouter(
    prefix="/code-actions",
    tags=["Code Actions"],
)


@router.post("/")
async def code_action(
    request: CodeActionRequest,
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
        action_type="code_suggestion",
        title=f"Generate {request.action} suggestion for {request.file_path}",
        details={
            "file_path": request.file_path,
            "action": request.action,
        },
    )

    try:
        result = await generate_code_action(
            request.owner,
            request.repo,
            request.file_path,
            request.code,
            request.action,
            user_id=user_id,
        )

        if not result:
            raise HTTPException(
                status_code=400,
                detail="Code suggestion could not be generated",
            )

        database.complete_activity(
            activity_id=activity["id"],
            user_id=user_id,
            workspace_id=workspace_id,
            status="success",
            details={
                "original_code": request.code,
                "modified_code": result,
            },
        )

        return {
            "original_code": request.code,
            "modified_code": result,
            "action": request.action,
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
