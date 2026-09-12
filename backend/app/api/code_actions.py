from fastapi import APIRouter

from app.schemas.code_actions import CodeActionRequest
from app.services.code_action_service import (
    generate_code_action,
)


router = APIRouter(
    prefix="/code-actions",
    tags=["Code Actions"],
)


@router.post("/")
async def code_action(
    request: CodeActionRequest,
):
    result = await generate_code_action(
        request.owner,
        request.repo,
        request.file_path,
        request.code,
        request.action,
    )

    return {
        "original_code": request.code,
        "modified_code": result,
        "action": request.action,
    }
