from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_auth_me_rejects_missing_session():
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_repository_endpoint_rejects_missing_session():
    response = client.get("/repositories/")
    assert response.status_code == 401


def test_chat_rejects_missing_session():
    response = client.post(
        "/chat/",
        json={
            "owner": "test-owner",
            "repo": "test-repo",
            "message": "Explain this repository",
            "history": [],
        },
    )
    assert response.status_code == 401
def test_auth_me_rejects_expired_session(monkeypatch):
    import time

    from app.api import auth

    expired_session = {
        "expires_at": time.time() - 60,
        "github_user": {
            "id": 12345,
            "login": "expired-test-user",
        },
        "access_token": "expired-test-token",
    }

    monkeypatch.setattr(
        auth,
        "get_session",
        lambda session_id: expired_session,
    )

    deleted = []
    monkeypatch.setattr(
        auth,
        "delete_session",
        lambda session_id: deleted.append(session_id),
    )

    response = client.get(
        "/auth/me",
        cookies={auth.SESSION_COOKIE: "expired-session-id"},
    )

    assert response.status_code == 401
    assert deleted == ["expired-session-id"]

def test_import_rejects_repository_user_cannot_access(monkeypatch):
    from fastapi import HTTPException
    from app.api import repositories
    from app.api.dependencies import get_current_session

    fake_session = {
        "github_user": {"id": 12345, "login": "security-test-user"},
        "access_token": "fake-test-token",
    }

    async def fake_get_current_session():
        return fake_session

    async def deny_repository_access(owner, repo, token):
        assert owner == "private-owner"
        assert repo == "private-repo"
        assert token == "fake-test-token"
        raise HTTPException(
            status_code=404,
            detail="Repository not found.",
        )

    monkeypatch.setattr(
        repositories,
        "get_accessible_repository",
        deny_repository_access,
    )

    app.dependency_overrides[get_current_session] = fake_get_current_session

    try:
        response = client.post(
            "/repositories/import",
            json={
                "url": "https://github.com/private-owner/private-repo"
            },
        )
    finally:
        app.dependency_overrides.pop(get_current_session, None)

    assert response.status_code == 404
    assert response.json()["detail"] == "Repository not found."

import pytest


@pytest.mark.parametrize(
    ("method", "url", "kwargs"),
    [
        ("post", "/index/?owner=test-owner&repo=test-repo", {}),
        ("post", "/repository-review/?owner=test-owner&repo=test-repo", {}),
        ("post", "/architecture-analysis/?owner=test-owner&repo=test-repo", {}),
        ("post", "/dependency-analysis/?owner=test-owner&repo=test-repo", {}),
        ("post", "/security-analysis/?owner=test-owner&repo=test-repo", {}),
        ("get", "/summary/?owner=test-owner&repo=test-repo", {}),
        ("get", "/repositories/tree?owner=test-owner&repo=test-repo", {}),
        (
            "get",
            "/repositories/file?owner=test-owner&repo=test-repo&path=README.md",
            {},
        ),
        (
            "get",
            "/repositories/search?owner=test-owner&repo=test-repo&query=README",
            {},
        ),
    ],
)
def test_protected_routes_reject_missing_session(method, url, kwargs):
    response = getattr(client, method)(url, **kwargs)
    assert response.status_code == 401

def test_logout_deletes_session_and_clears_cookie(monkeypatch):
    from app.api import auth

    deleted = []
    monkeypatch.setattr(
        auth,
        "delete_session",
        lambda session_id: deleted.append(session_id),
    )

    response = client.post(
        "/auth/logout",
        cookies={auth.SESSION_COOKIE: "logout-test-session"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Logged out successfully."
    assert deleted == ["logout-test-session"]

    set_cookie_headers = response.headers.get_list("set-cookie")
    assert any(
        auth.SESSION_COOKIE in header and "Max-Age=0" in header
        for header in set_cookie_headers
    )


def test_logout_without_session_is_safe(monkeypatch):
    from app.api import auth

    deleted = []
    monkeypatch.setattr(
        auth,
        "delete_session",
        lambda session_id: deleted.append(session_id),
    )

    response = client.post("/auth/logout")

    assert response.status_code == 200
    assert response.json()["message"] == "Logged out successfully."
    assert deleted == []

def test_import_returns_safe_error_for_unexpected_github_failure(monkeypatch):
    from fastapi import HTTPException
    from app.api import repositories
    from app.api.dependencies import get_current_session

    secret = "sensitive-response-content"
    fake_session = {
        "github_user": {"id": 12345, "login": "security-test-user"},
        "access_token": "fake-test-token",
    }

    async def fake_get_current_session():
        return fake_session

    async def fail_repository_access(owner, repo, token):
        raise HTTPException(
            status_code=502,
            detail="GitHub returned an unexpected error while accessing the repository.",
        )

    monkeypatch.setattr(
        repositories,
        "get_accessible_repository",
        fail_repository_access,
    )
    app.dependency_overrides[get_current_session] = fake_get_current_session

    try:
        response = client.post(
            "/repositories/import",
            json={"url": "https://github.com/private-owner/private-repo"},
        )
    finally:
        app.dependency_overrides.pop(get_current_session, None)

    assert response.status_code == 502
    assert secret not in response.text
    assert "fake-test-token" not in response.text
    assert "unexpected error" in response.json()["detail"]
def test_account_deletion_rejects_missing_session():
    response = client.request(
        "DELETE",
        "/auth/account",
        json={"confirm": True},
    )

    assert response.status_code == 401


def test_account_deletion_requires_confirmation(monkeypatch):
    from app.api import auth, dependencies

    fake_session = {
        "github_user": {"id": 12345, "login": "security-test-user"},
    }

    monkeypatch.setattr(
    dependencies,
    "get_valid_session",
    lambda session_id: fake_session,
)

    deleted = []
    monkeypatch.setattr(
        auth,
        "delete_user",
        lambda user_id: deleted.append(user_id) or True,
    )

    response = client.request(
        "DELETE",
        "/auth/account",
        json={"confirm": False},
        cookies={auth.SESSION_COOKIE: "account-test-session"},
    )

    assert response.status_code == 400
    assert deleted == []


def test_account_deletion_removes_account_and_clears_cookie(monkeypatch):
    from app.api import auth, dependencies

    fake_session = {
        "github_user": {"id": 12345, "login": "security-test-user"},
    }

    monkeypatch.setattr(
    dependencies,
    "get_valid_session",
    lambda session_id: fake_session,
)

    deleted = []
    monkeypatch.setattr(
        auth,
        "delete_user",
        lambda user_id: deleted.append(user_id) or True,
    )

    response = client.request(
        "DELETE",
        "/auth/account",
        json={"confirm": True},
        cookies={auth.SESSION_COOKIE: "account-test-session"},
    )

    assert response.status_code == 200
    assert deleted == [12345]
    assert any(
        auth.SESSION_COOKIE in header and "Max-Age=0" in header
        for header in response.headers.get_list("set-cookie")
    )


def test_account_deletion_rejects_invalid_user_id(monkeypatch):
    from app.api import auth, dependencies

    fake_session = {
        "github_user": {"id": "12345", "login": "security-test-user"},
    }

    monkeypatch.setattr(
    dependencies,
    "get_valid_session",
    lambda session_id: fake_session,
)

    deleted = []
    monkeypatch.setattr(
        auth,
        "delete_user",
        lambda user_id: deleted.append(user_id) or True,
    )

    response = client.request(
        "DELETE",
        "/auth/account",
        json={"confirm": True},
        cookies={auth.SESSION_COOKIE: "account-test-session"},
    )

    assert response.status_code == 401
    assert deleted == []