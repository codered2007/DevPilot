
import os
import secrets
import time
from urllib.parse import urlencode
from pydantic import BaseModel
from fastapi import Depends
from app.database import delete_user
import httpx
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse

from app.database import (
    initialize_database,
    save_session,
    get_session,
    delete_session,
    upsert_user,
)

load_dotenv()
initialize_database()

router = APIRouter(prefix="/auth", tags=["Authentication"])
class AccountDeletionRequest(BaseModel):
    confirm: bool
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"

GITHUB_CALLBACK_URL = os.getenv(
    "GITHUB_CALLBACK_URL",
    "http://localhost:8000/auth/github/callback",
)

FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    "http://localhost:5173",
).rstrip("/")

SESSION_COOKIE = "devpilot_session"
SESSION_MAX_AGE = 60 * 60 * 24 * 7

OAUTH_STATE_COOKIE = "devpilot_oauth_state"
OAUTH_STATE_MAX_AGE = 600

COOKIE_SECURE = (
    os.getenv("COOKIE_SECURE", "false").lower()
    in {"1", "true", "yes"}
)


def get_valid_session(session_id: str | None) -> dict | None:
    """Return a valid session and remove expired or malformed records."""
    if not session_id:
        return None

    session = get_session(session_id)

    if not isinstance(session, dict):
        if session is not None:
            delete_session(session_id)
        return None

    expires_at = session.get("expires_at")

    if (
        isinstance(expires_at, bool)
        or not isinstance(expires_at, (int, float))
        or time.time() >= expires_at
        or not isinstance(session.get("github_user"), dict)
        or not session.get("access_token")
    ):
        delete_session(session_id)
        return None

    return session


def clear_oauth_state_cookie(response):
    response.delete_cookie(
        key=OAUTH_STATE_COOKIE,
        path="/auth/github/callback",
        secure=COOKIE_SECURE,
        httponly=True,
        samesite="lax",
    )


@router.get("/github")
async def github_login():
    if not GITHUB_CLIENT_ID:
        raise HTTPException(
            status_code=500,
            detail="GITHUB_CLIENT_ID is not configured.",
        )

    state = secrets.token_urlsafe(32)

    params = {
        "client_id": GITHUB_CLIENT_ID,
        "redirect_uri": GITHUB_CALLBACK_URL,
        "scope": "repo read:user user:email",
        "state": state,
    }

    response = RedirectResponse(
        url=f"{GITHUB_AUTHORIZE_URL}?{urlencode(params)}"
    )

    response.set_cookie(
        key=OAUTH_STATE_COOKIE,
        value=state,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=OAUTH_STATE_MAX_AGE,
        path="/auth/github/callback",
    )

    return response


@router.get("/github/callback")
async def github_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
):
    expected_state = request.cookies.get(OAUTH_STATE_COOKIE)

    if (
        not state
        or not expected_state
        or not secrets.compare_digest(state, expected_state)
    ):
        response = JSONResponse(
            status_code=400,
            content={
                "detail": (
                    "Invalid or missing OAuth state. "
                    "Please try signing in again."
                )
            },
        )
        clear_oauth_state_cookie(response)
        return response

    if error:
        response = JSONResponse(
            status_code=400,
            content={
                "detail": "GitHub authorization was cancelled or denied."
            },
        )
        clear_oauth_state_cookie(response)
        return response

    if not code:
        response = JSONResponse(
            status_code=400,
            content={"detail": "GitHub authorization code is missing."},
        )
        clear_oauth_state_cookie(response)
        return response

    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        response = JSONResponse(
            status_code=500,
            content={
                "detail": "GitHub OAuth credentials are not configured."
            },
        )
        clear_oauth_state_cookie(response)
        return response

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            token_response = await client.post(
                GITHUB_TOKEN_URL,
                data={
                    "client_id": GITHUB_CLIENT_ID,
                    "client_secret": GITHUB_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": GITHUB_CALLBACK_URL,
                },
                headers={"Accept": "application/json"},
            )
            token_response.raise_for_status()
            token_data = token_response.json()

            access_token = token_data.get("access_token")

            if not access_token:
                response = JSONResponse(
                    status_code=401,
                    content={
                        "detail": (
                            "GitHub did not return an access token. "
                            "Please sign in again."
                        )
                    },
                )
                clear_oauth_state_cookie(response)
                return response

            user_response = await client.get(
                GITHUB_USER_URL,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                },
            )
            user_response.raise_for_status()
            github_user = user_response.json()

            if (
                not isinstance(github_user, dict)
                or not github_user.get("id")
                or not github_user.get("login")
            ):
                response = JSONResponse(
                    status_code=502,
                    content={
                        "detail": "GitHub returned an invalid user profile."
                    },
                )
                clear_oauth_state_cookie(response)
                return response

    except httpx.TimeoutException:
        response = JSONResponse(
            status_code=504,
            content={
                "detail": (
                    "GitHub authentication timed out. Please try again."
                )
            },
        )
        clear_oauth_state_cookie(response)
        return response

    except httpx.HTTPStatusError as exc:
        if exc.request.url == httpx.URL(GITHUB_TOKEN_URL):
            status_code = 401
            detail = (
                "GitHub authorization failed. Please sign in again."
            )
        else:
            status_code = 502
            detail = (
                "Could not verify your GitHub account. Please try again."
            )

        response = JSONResponse(
            status_code=status_code,
            content={"detail": detail},
        )
        clear_oauth_state_cookie(response)
        return response

    except (httpx.RequestError, ValueError):
        response = JSONResponse(
            status_code=502,
            content={
                "detail": "Could not complete GitHub authentication."
            },
        )
        clear_oauth_state_cookie(response)
        return response

    now = time.time()
    session_id = secrets.token_urlsafe(32)
    upsert_user(github_user)
    session_data = {
        "access_token": access_token,
        "github_user": {
            "id": github_user["id"],
            "login": github_user["login"],
            "name": github_user.get("name"),
            "avatar_url": github_user.get("avatar_url"),
            "email": github_user.get("email"),
        },
        "created_at": now,
        "expires_at": now + SESSION_MAX_AGE,
    }

    save_session(session_id, session_data)

    response = RedirectResponse(
        url=f"{FRONTEND_URL}/dashboard"
    )

    response.set_cookie(
        key=SESSION_COOKIE,
        value=session_id,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=SESSION_MAX_AGE,
        path="/",
    )

    clear_oauth_state_cookie(response)

    return response


@router.get("/me")
async def get_current_user(request: Request):
    session_id = request.cookies.get(SESSION_COOKIE)
    session = get_valid_session(session_id)

    if not session:
        response = JSONResponse(
            status_code=401,
            content={
                "detail": (
                    "Session expired or invalid. Please sign in again."
                )
            },
        )
        response.delete_cookie(
            key=SESSION_COOKIE,
            path="/",
            secure=COOKIE_SECURE,
            httponly=True,
            samesite="lax",
        )
        return response

    return {"user": session["github_user"]}


@router.post("/logout")
async def logout(request: Request):
    session_id = request.cookies.get(SESSION_COOKIE)

    if session_id:
        delete_session(session_id)

    response = JSONResponse(
        content={"message": "Logged out successfully."}
    )

    response.delete_cookie(
        key=SESSION_COOKIE,
        path="/",
        secure=COOKIE_SECURE,
        httponly=True,
        samesite="lax",
    )

    clear_oauth_state_cookie(response)

    return response

@router.delete("/account")
def delete_account(
    payload: AccountDeletionRequest,
    request: Request,
):
    from app.api.dependencies import get_current_session

    session = get_current_session(request)
    if payload.confirm is not True:
        raise HTTPException(
            status_code=400,
            detail="Explicit account deletion confirmation is required.",
        )

    github_user = session.get("github_user", {})
    user_id = github_user.get("id")

    if not isinstance(user_id, int) or isinstance(user_id, bool):
        raise HTTPException(
            status_code=401,
            detail="Invalid user identity. Please sign in again.",
        )

    deleted = delete_user(user_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Account not found.",
        )

    response = JSONResponse(
    content={
        "message": "Account deleted successfully.",
        "chroma_cleanup": "pending",
        "note": "Repository vector data is queued for cleanup.",
    }
)

    response.delete_cookie(
        key=SESSION_COOKIE,
        path="/",
        secure=COOKIE_SECURE,
        httponly=True,
        samesite="lax",
    )

    clear_oauth_state_cookie(response)

    return response
