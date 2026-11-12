from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.dependencies import get_current_session
from app import database


router = APIRouter(
    prefix="/preferences",
    tags=["User Preferences"],
)


class PreferencesUpdate(BaseModel):
    preferences: dict


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


@router.get("/")
async def get_preferences(
    session: dict = Depends(get_current_session),
):
    user_id = get_user_id(session)

    preferences = database.get_user_preferences(user_id)

    return {"preferences": preferences}


@router.put("/")
async def update_preferences(
    payload: PreferencesUpdate,
    session: dict = Depends(get_current_session),
):
    user_id = get_user_id(session)

    try:
        preferences = database.update_user_preferences(
            user_id=user_id,
            preferences=payload.preferences,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from None

    return {"preferences": preferences}


@router.delete("/")
async def delete_preferences(
    session: dict = Depends(get_current_session),
):
    user_id = get_user_id(session)

    deleted = database.delete_user_preferences(user_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="User preferences not found.",
        )

    return {"message": "User preferences deleted."}