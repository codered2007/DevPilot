
import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException

from app.main import app
from app.api.dependencies import get_current_session
from app.api import pull_request as pull_request_api
from app import database


@pytest.fixture
def pull_request_api_client(tmp_path, monkeypatch):
    monkeypatch.setattr(
        database,
        "DATABASE_PATH",
        tmp_path / "pull_request_api.db",
    )

    database.initialize_database()

    database.upsert_user({
        "id": 1001,
        "login": "test-user",
        "name": "Test User",
    })

    app.dependency_overrides[get_current_session] = lambda: {
        "access_token": "test-token",
        "github_user": {
            "id": 1001,
            "login": "test-user",
        },
    }

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def pull_request_payload():
    return {
        "owner": "test-owner",
        "repo": "test-repo",
        "title": "Fix authentication bug",
        "body": "This PR fixes the authentication issue.",
        "head": "fix/authentication",
        "base": "main",
    }


def test_pull_request_creates_successful_activity(
    pull_request_api_client,
    pull_request_payload,
    monkeypatch,
):
    async def mock_accessible_repository(*args, **kwargs):
        return {"full_name": "test-owner/test-repo"}

    async def mock_create_pull_request(*args, **kwargs):
        return {
            "number": 42,
            "title": "Fix authentication bug",
            "url": "https://github.com/test-owner/test-repo/pull/42",
            "state": "open",
            "head": "fix/authentication",
            "base": "main",
        }

    monkeypatch.setattr(
        pull_request_api,
        "get_accessible_repository",
        mock_accessible_repository,
    )
    monkeypatch.setattr(
        pull_request_api,
        "create_pull_request",
        mock_create_pull_request,
    )

    response = pull_request_api_client.post(
        "/pull-request/",
        json=pull_request_payload,
    )

    assert response.status_code == 200
    assert response.json()["number"] == 42

    activities = database.list_activities(
        user_id=1001,
        owner="test-owner",
        repo="test-repo",
    )

    assert len(activities) == 1

    activity = activities[0]

    assert activity["action_type"] == "pull_request"
    assert activity["status"] == "success"
    assert activity["details"]["number"] == 42
    assert activity["details"]["title"] == "Fix authentication bug"
    assert activity["details"]["url"] == (
        "https://github.com/test-owner/test-repo/pull/42"
    )
    assert activity["details"]["state"] == "open"
    assert activity["details"]["head"] == "fix/authentication"
    assert activity["details"]["base"] == "main"


def test_pull_request_records_failed_activity(
    pull_request_api_client,
    pull_request_payload,
    monkeypatch,
):
    async def mock_accessible_repository(*args, **kwargs):
        return {"full_name": "test-owner/test-repo"}

    async def mock_create_pull_request(*args, **kwargs):
        raise RuntimeError("Pull request creation failed")

    monkeypatch.setattr(
        pull_request_api,
        "get_accessible_repository",
        mock_accessible_repository,
    )
    monkeypatch.setattr(
        pull_request_api,
        "create_pull_request",
        mock_create_pull_request,
    )

    response = pull_request_api_client.post(
        "/pull-request/",
        json=pull_request_payload,
    )

    assert response.status_code == 500

    activities = database.list_activities(
        user_id=1001,
        owner="test-owner",
        repo="test-repo",
    )

    assert len(activities) == 1
    assert activities[0]["action_type"] == "pull_request"
    assert activities[0]["status"] == "failed"
    assert activities[0]["details"]["error_type"] == "RuntimeError"


def test_pull_request_empty_result_records_failure(
    pull_request_api_client,
    pull_request_payload,
    monkeypatch,
):
    async def mock_accessible_repository(*args, **kwargs):
        return {"full_name": "test-owner/test-repo"}

    async def mock_create_pull_request(*args, **kwargs):
        return None

    monkeypatch.setattr(
        pull_request_api,
        "get_accessible_repository",
        mock_accessible_repository,
    )
    monkeypatch.setattr(
        pull_request_api,
        "create_pull_request",
        mock_create_pull_request,
    )

    response = pull_request_api_client.post(
        "/pull-request/",
        json=pull_request_payload,
    )

    assert response.status_code == 400

    activities = database.list_activities(
        user_id=1001,
        owner="test-owner",
        repo="test-repo",
    )

    assert len(activities) == 1
    assert activities[0]["status"] == "failed"
    assert activities[0]["details"]["error_type"] == "HTTPException"


def test_pull_request_access_denial_creates_no_activity(
    pull_request_api_client,
    pull_request_payload,
    monkeypatch,
):
    async def mock_accessible_repository(*args, **kwargs):
        raise HTTPException(
            status_code=403,
            detail="Repository access denied",
        )

    monkeypatch.setattr(
        pull_request_api,
        "get_accessible_repository",
        mock_accessible_repository,
    )

    response = pull_request_api_client.post(
        "/pull-request/",
        json=pull_request_payload,
    )

    assert response.status_code == 403

    activities = database.list_activities(user_id=1001)

    assert activities == []
