
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.dependencies import get_current_session
from app import database


router = APIRouter(
    prefix="/saved-results",
    tags=["Saved Results"],
)


ALLOWED_RESULT_TYPES = {
    "summary",
    "review",
    "architecture",
    "dependency",
    "security",
}


class SavedResultCreate(BaseModel):
    workspace_id: str = Field(min_length=1, max_length=100)
    owner: str = Field(min_length=1, max_length=100)
    repo: str = Field(min_length=1, max_length=100)
    result_type: str
    title: str = Field(min_length=1, max_length=200)
    content: dict

    model_config = {"str_strip_whitespace": True}


def get_user_id(session: dict) -> int:
    github_user = session.get("github_user", {})
    user_id = (
        github_user.get("id")
        if isinstance(github_user, dict)
        else None
    )

    if (
        not isinstance(user_id, int)
        or isinstance(user_id, bool)
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid authenticated user.",
        )

    return user_id


def handle_workspace_error(exc: ValueError):
    if str(exc) == "Workspace not found.":
        raise HTTPException(
            status_code=404,
            detail="Workspace not found.",
        ) from None

    raise HTTPException(
        status_code=422,
        detail=str(exc),
    ) from None


@router.post("/", status_code=201)
async def create_saved_result(
    payload: SavedResultCreate,
    session: dict = Depends(get_current_session),
):
    user_id = get_user_id(session)

    if payload.result_type not in ALLOWED_RESULT_TYPES:
        raise HTTPException(
            status_code=422,
            detail="Invalid saved result type.",
        )

    try:
        result = database.save_result(
            user_id=user_id,
            workspace_id=payload.workspace_id,
            owner=payload.owner,
            repo=payload.repo,
            result_type=payload.result_type,
            title=payload.title,
            content=payload.content,
        )
    except ValueError as exc:
        handle_workspace_error(exc)

    return {"saved_result": result}


@router.get("/")
async def list_user_saved_results(
    workspace_id: str = Query(..., min_length=1, max_length=100),
    owner: str | None = None,
    repo: str | None = None,
    result_type: str | None = None,
    limit: int = Query(default=100, ge=1, le=100),
    session: dict = Depends(get_current_session),
):
    user_id = get_user_id(session)

    if (owner is None) != (repo is None):
        raise HTTPException(
            status_code=400,
            detail="Both owner and repo must be provided together.",
        )

    if (
        result_type is not None
        and result_type not in ALLOWED_RESULT_TYPES
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid saved result type.",
        )

    try:
        results = database.list_saved_results(
            user_id=user_id,
            workspace_id=workspace_id,
            owner=owner,
            repo=repo,
            result_type=result_type,
            limit=limit,
        )
    except ValueError as exc:
        handle_workspace_error(exc)

    return {
        "saved_results": results,
        "count": len(results),
    }


@router.get("/{result_id}")
async def get_user_saved_result(
    result_id: str,
    workspace_id: str = Query(..., min_length=1, max_length=100),
    session: dict = Depends(get_current_session),
):
    user_id = get_user_id(session)

    result = database.get_saved_result(
        result_id=result_id,
        user_id=user_id,
        workspace_id=workspace_id,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Saved result not found.",
        )

    return {"saved_result": result}


@router.delete("/{result_id}")
async def remove_user_saved_result(
    result_id: str,
    workspace_id: str = Query(..., min_length=1, max_length=100),
    session: dict = Depends(get_current_session),
):
    user_id = get_user_id(session)

    deleted = database.delete_saved_result(
        result_id=result_id,
        user_id=user_id,
        workspace_id=workspace_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Saved result not found.",
        )

    return {"message": "Saved result deleted."}
