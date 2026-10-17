
from fastapi import HTTPException, Request

from app.api.auth import SESSION_COOKIE, get_valid_session


def get_current_session(request: Request) -> dict:
    session_id = request.cookies.get(SESSION_COOKIE)
    session = get_valid_session(session_id)

    if not session:
        raise HTTPException(
            status_code=401,
            detail="Session expired or invalid. Please sign in again.",
        )

    return session
