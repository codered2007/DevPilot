
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.api.dependencies import get_current_session
from app.api import summary as summary_api
from app import database


@pytest.fixture
def summary_api_client(tmp_path, monkeypatch):
    monkeypatch.setattr(
        database,
        "DATABASE_PATH",
        tmp_path / "summary_api.db",
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


def test_repository_summary_creates_successful_activity(
    summary_api_client,
    monkeypatch,
):
    async def mock_accessible_repository(*args, **kwargs):
        return {"full_name": "test-owner/test-repo"}

    async def mock_summarize_repository(*args, **kwargs):
        return "This is a test repository summary."

    monkeypatch.setattr(
        summary_api,
        "get_accessible_repository",
        mock_accessible_repository,
    )
    monkeypatch.setattr(
        summary_api,
        "summarize_repository",
        mock_summarize_repository,
    )

    response = summary_api_client.get(
        "/summary/",
        params={"owner": "test-owner", "repo": "test-repo"},
    )

    assert response.status_code == 200
    assert response.json()["summary"] == (
        "This is a test repository summary."
    )

    activities = database.list_activities(
        user_id=1001,
        owner="test-owner",
        repo="test-repo",
    )

    assert len(activities) == 1
    assert activities[0]["action_type"] == "repository_summary"
    assert activities[0]["status"] == "success"


def test_repository_summary_records_failed_activity(
    summary_api_client,
    monkeypatch,
):
    async def mock_accessible_repository(*args, **kwargs):
        return {"full_name": "test-owner/test-repo"}

    async def mock_summarize_repository(*args, **kwargs):
        raise RuntimeError("Summary generation failed")

    monkeypatch.setattr(
        summary_api,
        "get_accessible_repository",
        mock_accessible_repository,
    )
    monkeypatch.setattr(
        summary_api,
        "summarize_repository",
        mock_summarize_repository,
    )

    response = summary_api_client.get(
        "/summary/",
        params={"owner": "test-owner", "repo": "test-repo"},
    )

    assert response.status_code == 500

    activities = database.list_activities(user_id=1001)

    assert len(activities) == 1
    assert activities[0]["action_type"] == "repository_summary"
    assert activities[0]["status"] == "failed"
    assert activities[0]["details"]["error_type"] == "RuntimeError"


def test_repository_summary_empty_result_records_failure(
    summary_api_client,
    monkeypatch,
):
    async def mock_accessible_repository(*args, **kwargs):
        return {"full_name": "test-owner/test-repo"}

    async def mock_summarize_repository(*args, **kwargs):
        return None

    monkeypatch.setattr(
        summary_api,
        "get_accessible_repository",
        mock_accessible_repository,
    )
    monkeypatch.setattr(
        summary_api,
        "summarize_repository",
        mock_summarize_repository,
    )

    response = summary_api_client.get(
        "/summary/",
        params={"owner": "test-owner", "repo": "test-repo"},
    )

    assert response.status_code == 400

    activities = database.list_activities(user_id=1001)

    assert len(activities) == 1
    assert activities[0]["action_type"] == "repository_summary"
    assert activities[0]["status"] == "failed"
    assert activities[0]["details"]["error_type"] == "HTTPException"


def test_repository_summary_access_denial_creates_no_activity(
    summary_api_client,
    monkeypatch,
):
    async def mock_accessible_repository(*args, **kwargs):
        raise HTTPException(
            status_code=403,
            detail="Repository access denied",
        )

    monkeypatch.setattr(
        summary_api,
        "get_accessible_repository",
        mock_accessible_repository,
    )

    response = summary_api_client.get(
        "/summary/",
        params={"owner": "test-owner", "repo": "test-repo"},
    )

    assert response.status_code == 403
    assert database.list_activities(user_id=1001) == []
