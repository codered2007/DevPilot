import os
import secrets
from urllib.parse import urlencode

import httpx
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse

load_dotenv()

router = APIRouter(prefix="/auth", tags=["Authentication"])

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"

GITHUB_CALLBACK_URL = (
    "http://localhost:8000/auth/github/callback"
)

FRONTEND_URL = "http://localhost:5173"

# Temporary in-memory session store.
# The GitHub access token stays on the backend.
sessions: dict[str, dict] = {}


@router.get("/github")
async def github_login():
    if not GITHUB_CLIENT_ID:
        raise HTTPException(
            status_code=500,
            detail="GITHUB_CLIENT_ID is not configured.",
        )

    params = {
        "client_id": GITHUB_CLIENT_ID,
        "redirect_uri": GITHUB_CALLBACK_URL,
        "scope": "read:user user:email",
    }

    authorization_url = (
        f"{GITHUB_AUTHORIZE_URL}?{urlencode(params)}"
    )

    return RedirectResponse(
        url=authorization_url
    )


@router.get("/github/callback")
async def github_callback(
    code: str | None = None,
):
    if not code:
        raise HTTPException(
            status_code=400,
            detail="GitHub authorization code is missing.",
        )

    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="GitHub OAuth credentials are not configured.",
        )

    async with httpx.AsyncClient() as client:
        # Exchange OAuth code for GitHub access token.
        token_response = await client.post(
            GITHUB_TOKEN_URL,
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
            },
            headers={
                "Accept": "application/json",
            },
        )

        token_response.raise_for_status()

        token_data = token_response.json()
        access_token = token_data.get("access_token")

        if not access_token:
            raise HTTPException(
                status_code=400,
                detail="GitHub did not return an access token.",
            )

        # Retrieve authenticated GitHub user.
        user_response = await client.get(
            GITHUB_USER_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
            },
        )

        user_response.raise_for_status()

        github_user = user_response.json()

    # Generate an opaque session ID.
    session_id = secrets.token_urlsafe(32)

    # Keep sensitive GitHub token on the backend.
    sessions[session_id] = {
        "access_token": access_token,
        "github_user": {
            "id": github_user.get("id"),
            "login": github_user.get("login"),
            "name": github_user.get("name"),
            "avatar_url": github_user.get("avatar_url"),
            "email": github_user.get("email"),
        },
    }

    response = RedirectResponse(
        url=f"{FRONTEND_URL}/dashboard"
    )

    response.set_cookie(
        key="devpilot_session",
        value=session_id,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
        path="/",
    )

    return response


@router.get("/me")
async def get_current_user(
    request: Request,
):
    session_id = request.cookies.get(
        "devpilot_session"
    )

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

    return {
        "user": session["github_user"]
    }


@router.post("/logout")
async def logout(
    request: Request,
):
    session_id = request.cookies.get(
        "devpilot_session"
    )

    if session_id:
        sessions.pop(
            session_id,
            None,
        )

    response = JSONResponse(
        content={
            "message": "Logged out successfully."
        }
    )

    response.delete_cookie(
        key="devpilot_session",
        path="/",
    )

    return response