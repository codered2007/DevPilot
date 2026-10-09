from fastapi import HTTPException, Request

from app.api.auth import sessions


def get_current_session(request: Request) -> dict:
    session_id = request.cookies.get("devpilot_session")

    if not session_id:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated.",
        )

    session = sessions.get(session_id)

    if not session:
        raise HTTPException(
            status_code=401,
            detail="Session expired or invalid.",
        )

    return session