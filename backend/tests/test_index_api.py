
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.api.dependencies import get_current_session
from app.api import index as index_api
from app import database


@pytest.fixture
def index_api_client(tmp_path, monkeypatch):
    monkeypatch.setattr(
        database,
        "DATABASE_PATH",
        tmp_path / "index_api.db",
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


def test_index_creates_successful_activity(
    index_api_client,
    monkeypatch,
):
    async def mock_accessible_repository(*args, **kwargs):
        return {"full_name": "test-owner/test-repo"}

    async def mock_index_repository(*args, **kwargs):
        return {
            "indexed_files": 5,
            "indexed_chunks": 18,
        }

    monkeypatch.setattr(
        index_api,
        "get_accessible_repository",
        mock_accessible_repository,
    )
    monkeypatch.setattr(
        index_api,
        "index_repository",
        mock_index_repository,
    )

    response = index_api_client.post(
        "/index/",
        params={"owner": "test-owner", "repo": "test-repo",
        "workspace_id": "test-workspace-1001", "workspace_id": "test-workspace-1001"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "indexed_files": 5,
        "indexed_chunks": 18,
    }

    activities = database.list_activities(
        user_id=1001,
        workspace_id="test-workspace-1001",
        owner="test-owner",
        repo="test-repo",
    )

    assert len(activities) == 1
    assert activities[0]["action_type"] == "index"
    assert activities[0]["status"] == "success"
    assert activities[0]["details"]["indexed_files"] == 5
    assert activities[0]["details"]["indexed_chunks"] == 18
    assert activities[0]["completed_at"] is not None


def test_index_records_failed_activity(
    index_api_client,
    monkeypatch,
):
    async def mock_accessible_repository(*args, **kwargs):
        return {"full_name": "test-owner/test-repo"}

    async def mock_index_repository(*args, **kwargs):
        raise RuntimeError("Indexing failed")

    monkeypatch.setattr(
        index_api,
        "get_accessible_repository",
        mock_accessible_repository,
    )
    monkeypatch.setattr(
        index_api,
        "index_repository",
        mock_index_repository,
    )

    response = index_api_client.post(
        "/index/",
        params={"owner": "test-owner", "repo": "test-repo",
        "workspace_id": "test-workspace-1001", "workspace_id": "test-workspace-1001"},
    )

    assert response.status_code == 500

    activities = database.list_activities(
        user_id=1001,
        workspace_id="test-workspace-1001",
        owner="test-owner",
        repo="test-repo",
    )

    assert len(activities) == 1
    assert activities[0]["status"] == "failed"
    assert activities[0]["details"]["error_type"] == "RuntimeError"
    assert activities[0]["completed_at"] is not None


def test_index_does_not_record_activity_when_access_is_denied(
    index_api_client,
    monkeypatch,
):
    async def mock_accessible_repository(*args, **kwargs):
        raise HTTPException(
            status_code=403,
            detail="Repository access denied",
        )

    monkeypatch.setattr(
        index_api,
        "get_accessible_repository",
        mock_accessible_repository,
    )

    response = index_api_client.post(
        "/index/",
        params={"owner": "test-owner", "repo": "test-repo",
        "workspace_id": "test-workspace-1001", "workspace_id": "test-workspace-1001"},
    )

    assert response.status_code == 403

    activities = database.list_activities(user_id=1001, workspace_id="test-workspace-1001")

    assert activities == []

