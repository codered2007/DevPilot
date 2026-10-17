from fastapi import APIRouter, Depends

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
    session: dict = Depends(get_current_session),
):
    await get_accessible_repository(
        request.owner,
        request.repo,
        session["access_token"],
    )

    result = await generate_code_action(
        request.owner,
        request.repo,
        request.file_path,
        request.code,
        request.action,
        user_id=session["github_user"]["id"],
    )

    return {
        "original_code": request.code,
        "modified_code": result,
        "action": request.action,
    }