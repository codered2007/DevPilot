
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.api.dependencies import get_current_session
from app.api import repository_review as review_api
from app import database


@pytest.fixture
def review_api_client(tmp_path, monkeypatch):
    monkeypatch.setattr(
        database,
        "DATABASE_PATH",
        tmp_path / "review_api.db",
    )

    database.initialize_database()

    database.upsert_user({
        "id": 1001,
        "login": "test-user",
        "name": "Test User",
    })

    database.create_workspace(
        "test-workspace-1001",
        1001,
        "Test Workspace",
    )

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


def test_repository_review_creates_successful_activity(
    review_api_client,
    monkeypatch,
):
    async def mock_accessible_repository(*args, **kwargs):
        return {"full_name": "test-owner/test-repo"}

    async def mock_review_repository(*args, **kwargs):
        return {"summary": "Review completed", "issues": []}

    monkeypatch.setattr(
        review_api,
        "get_accessible_repository",
        mock_accessible_repository,
    )
    monkeypatch.setattr(
        review_api,
        "review_repository",
        mock_review_repository,
    )

    response = review_api_client.post(
        "/repository-review/",
        params={"owner": "test-owner", "repo": "test-repo",
        "workspace_id": "test-workspace-1001", "workspace_id": "test-workspace-1001"},
    )

    assert response.status_code == 200
    assert response.json()["summary"] == "Review completed"

    activities = database.list_activities(
        user_id=1001,
        workspace_id="test-workspace-1001",
        owner="test-owner",
        repo="test-repo",
    )

    assert len(activities) == 1
    assert activities[0]["action_type"] == "repository_review"
    assert activities[0]["status"] == "success"


def test_repository_review_records_failed_activity(
    review_api_client,
    monkeypatch,
):
    async def mock_accessible_repository(*args, **kwargs):
        return {"full_name": "test-owner/test-repo"}

    async def mock_review_repository(*args, **kwargs):
        raise RuntimeError("Review failed")

    monkeypatch.setattr(
        review_api,
        "get_accessible_repository",
        mock_accessible_repository,
    )
    monkeypatch.setattr(
        review_api,
        "review_repository",
        mock_review_repository,
    )

    response = review_api_client.post(
        "/repository-review/",
        params={"owner": "test-owner", "repo": "test-repo",
        "workspace_id": "test-workspace-1001", "workspace_id": "test-workspace-1001"},
    )

    assert response.status_code == 502

    activities = database.list_activities(
        user_id=1001,
        workspace_id="test-workspace-1001",
        owner="test-owner",
        repo="test-repo",
    )

    assert len(activities) == 1
    assert activities[0]["status"] == "failed"
    assert activities[0]["details"]["error_type"] == "RuntimeError"


def test_repository_review_empty_result_records_failure(
    review_api_client,
    monkeypatch,
):
    async def mock_accessible_repository(*args, **kwargs):
        return {"full_name": "test-owner/test-repo"}

    async def mock_review_repository(*args, **kwargs):
        return None

    monkeypatch.setattr(
        review_api,
        "get_accessible_repository",
        mock_accessible_repository,
    )
    monkeypatch.setattr(
        review_api,
        "review_repository",
        mock_review_repository,
    )

    response = review_api_client.post(
        "/repository-review/",
        params={"owner": "test-owner", "repo": "test-repo",
        "workspace_id": "test-workspace-1001", "workspace_id": "test-workspace-1001"},
    )

    assert response.status_code == 502

    activities = database.list_activities(user_id=1001, workspace_id="test-workspace-1001")

    assert len(activities) == 1
    assert activities[0]["status"] == "failed"
    assert activities[0]["details"]["error_type"] == "HTTPException"


def test_repository_review_access_denial_creates_no_activity(
    review_api_client,
    monkeypatch,
):
    async def mock_accessible_repository(*args, **kwargs):
        raise HTTPException(
            status_code=403,
            detail="Repository access denied",
        )

    monkeypatch.setattr(
        review_api,
        "get_accessible_repository",
        mock_accessible_repository,
    )

    response = review_api_client.post(
        "/repository-review/",
        params={"owner": "test-owner", "repo": "test-repo",
        "workspace_id": "test-workspace-1001", "workspace_id": "test-workspace-1001"},
    )

    assert response.status_code == 403
    assert database.list_activities(user_id=1001, workspace_id="test-workspace-1001") == []

