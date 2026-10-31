
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.dependencies import get_current_session
from app.database import (
    create_workspace,
    delete_workspace,
    list_workspaces,
)

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


def _current_user_id(session: dict) -> int:
    github_user = session.get("github_user", {})
    user_id = github_user.get("id")

    if not isinstance(user_id, int) or isinstance(user_id, bool):
        raise HTTPException(
            status_code=401,
            detail="Invalid user identity. Please sign in again.",
        )

    return user_id


@router.get("")
def get_workspaces(
    session: dict = Depends(get_current_session),
):
    user_id = _current_user_id(session)
    return {"workspaces": list_workspaces(user_id)}


@router.post("", status_code=201)
def post_workspace(
    payload: WorkspaceCreate,
    session: dict = Depends(get_current_session),
):
    user_id = _current_user_id(session)
    name = payload.name.strip()

    if not name:
        raise HTTPException(
            status_code=422,
            detail="Workspace name cannot be blank.",
        )

    workspace_id = str(uuid4())

    try:
        create_workspace(workspace_id, user_id, name)
    except Exception:
        # Do not expose internal database errors to clients.
        raise HTTPException(
            status_code=500,
            detail="Unable to create workspace.",
        ) from None

    return {
        "workspace": {
            "id": workspace_id,
            "user_id": user_id,
            "name": name,
        }
    }


@router.delete("/{workspace_id}")
def remove_workspace(
    workspace_id: str,
    session: dict = Depends(get_current_session),
):
    user_id = _current_user_id(session)

    if not delete_workspace(workspace_id, user_id):
        raise HTTPException(
            status_code=404,
            detail="Workspace not found.",
        )

    return {"message": "Workspace deleted."}
