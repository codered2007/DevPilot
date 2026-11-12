
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.api.dependencies import get_current_session
from app.api import dependency_analysis as dependency_api
from app import database


@pytest.fixture
def dependency_api_client(tmp_path, monkeypatch):
    monkeypatch.setattr(
        database,
        "DATABASE_PATH",
        tmp_path / "dependency_api.db",
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


def test_dependency_analysis_creates_successful_activity(
    dependency_api_client,
    monkeypatch,
):
    async def mock_accessible_repository(*args, **kwargs):
        return {"full_name": "test-owner/test-repo"}

    async def mock_analyze_dependencies(*args, **kwargs):
        return {"dependencies": ["fastapi", "pytest"]}

    monkeypatch.setattr(
        dependency_api,
        "get_accessible_repository",
        mock_accessible_repository,
    )
    monkeypatch.setattr(
        dependency_api,
        "analyze_repository_dependencies",
        mock_analyze_dependencies,
    )

    response = dependency_api_client.post(
        "/dependency-analysis/",
        params={"owner": "test-owner", "repo": "test-repo",
        "workspace_id": "test-workspace-1001", "workspace_id": "test-workspace-1001"},
    )

    assert response.status_code == 200
    assert response.json()["dependencies"] == ["fastapi", "pytest"]

    activities = database.list_activities(
        user_id=1001,
        workspace_id="test-workspace-1001",
        owner="test-owner",
        repo="test-repo",
    )

    assert len(activities) == 1
    assert activities[0]["action_type"] == "dependency_analysis"
    assert activities[0]["status"] == "success"


def test_dependency_analysis_records_failed_activity(
    dependency_api_client,
    monkeypatch,
):
    async def mock_accessible_repository(*args, **kwargs):
        return {"full_name": "test-owner/test-repo"}

    async def mock_analyze_dependencies(*args, **kwargs):
        raise RuntimeError("Dependency analysis failed")

    monkeypatch.setattr(
        dependency_api,
        "get_accessible_repository",
        mock_accessible_repository,
    )
    monkeypatch.setattr(
        dependency_api,
        "analyze_repository_dependencies",
        mock_analyze_dependencies,
    )

    response = dependency_api_client.post(
        "/dependency-analysis/",
        params={"owner": "test-owner", "repo": "test-repo",
        "workspace_id": "test-workspace-1001", "workspace_id": "test-workspace-1001"},
    )

    assert response.status_code == 500

    activities = database.list_activities(user_id=1001, workspace_id="test-workspace-1001")

    assert len(activities) == 1
    assert activities[0]["action_type"] == "dependency_analysis"
    assert activities[0]["status"] == "failed"
    assert activities[0]["details"]["error_type"] == "RuntimeError"


def test_dependency_analysis_empty_result_records_failure(
    dependency_api_client,
    monkeypatch,
):
    async def mock_accessible_repository(*args, **kwargs):
        return {"full_name": "test-owner/test-repo"}

    async def mock_analyze_dependencies(*args, **kwargs):
        return None

    monkeypatch.setattr(
        dependency_api,
        "get_accessible_repository",
        mock_accessible_repository,
    )
    monkeypatch.setattr(
        dependency_api,
        "analyze_repository_dependencies",
        mock_analyze_dependencies,
    )

    response = dependency_api_client.post(
        "/dependency-analysis/",
        params={"owner": "test-owner", "repo": "test-repo",
        "workspace_id": "test-workspace-1001", "workspace_id": "test-workspace-1001"},
    )

    assert response.status_code == 400

    activities = database.list_activities(user_id=1001, workspace_id="test-workspace-1001")

    assert len(activities) == 1
    assert activities[0]["action_type"] == "dependency_analysis"
    assert activities[0]["status"] == "failed"
    assert activities[0]["details"]["error_type"] == "HTTPException"


def test_dependency_analysis_access_denial_creates_no_activity(
    dependency_api_client,
    monkeypatch,
):
    async def mock_accessible_repository(*args, **kwargs):
        raise HTTPException(
            status_code=403,
            detail="Repository access denied",
        )

    monkeypatch.setattr(
        dependency_api,
        "get_accessible_repository",
        mock_accessible_repository,
    )

    response = dependency_api_client.post(
        "/dependency-analysis/",
        params={"owner": "test-owner", "repo": "test-repo",
        "workspace_id": "test-workspace-1001", "workspace_id": "test-workspace-1001"},
    )

    assert response.status_code == 403
    assert database.list_activities(user_id=1001, workspace_id="test-workspace-1001") == []

