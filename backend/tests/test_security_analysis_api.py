
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.api.dependencies import get_current_session
from app.api import security_analysis as security_api
from app import database


@pytest.fixture
def security_api_client(tmp_path, monkeypatch):
    monkeypatch.setattr(
        database,
        "DATABASE_PATH",
        tmp_path / "security_api.db",
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


def test_security_analysis_creates_successful_activity(
    security_api_client,
    monkeypatch,
):
    async def mock_accessible_repository(*args, **kwargs):
        return {"full_name": "test-owner/test-repo"}

    async def mock_analyze_dependencies(*args, **kwargs):
        return {"dependencies": ["fastapi", "pytest"]}

    async def mock_analyze_security(*args, **kwargs):
        return {"vulnerabilities": [], "summary": "No vulnerabilities found"}

    monkeypatch.setattr(
        security_api,
        "get_accessible_repository",
        mock_accessible_repository,
    )
    monkeypatch.setattr(
        security_api,
        "analyze_repository_dependencies",
        mock_analyze_dependencies,
    )
    monkeypatch.setattr(
        security_api,
        "analyze_repository_security",
        mock_analyze_security,
    )

    response = security_api_client.post(
        "/security-analysis/",
        params={"owner": "test-owner", "repo": "test-repo"},
    )

    assert response.status_code == 200
    assert response.json()["summary"] == "No vulnerabilities found"

    activities = database.list_activities(
        user_id=1001,
        owner="test-owner",
        repo="test-repo",
    )

    assert len(activities) == 1
    assert activities[0]["action_type"] == "security_analysis"
    assert activities[0]["status"] == "success"


def test_security_analysis_dependency_failure_records_activity(
    security_api_client,
    monkeypatch,
):
    async def mock_accessible_repository(*args, **kwargs):
        return {"full_name": "test-owner/test-repo"}

    async def mock_analyze_dependencies(*args, **kwargs):
        raise RuntimeError("Dependency analysis failed")

    monkeypatch.setattr(
        security_api,
        "get_accessible_repository",
        mock_accessible_repository,
    )
    monkeypatch.setattr(
        security_api,
        "analyze_repository_dependencies",
        mock_analyze_dependencies,
    )

    response = security_api_client.post(
        "/security-analysis/",
        params={"owner": "test-owner", "repo": "test-repo"},
    )

    assert response.status_code == 500

    activities = database.list_activities(user_id=1001)

    assert len(activities) == 1
    assert activities[0]["action_type"] == "security_analysis"
    assert activities[0]["status"] == "failed"
    assert activities[0]["details"]["error_type"] == "RuntimeError"


def test_security_analysis_failure_records_activity(
    security_api_client,
    monkeypatch,
):
    async def mock_accessible_repository(*args, **kwargs):
        return {"full_name": "test-owner/test-repo"}

    async def mock_analyze_dependencies(*args, **kwargs):
        return {"dependencies": ["fastapi"]}

    async def mock_analyze_security(*args, **kwargs):
        raise RuntimeError("Security analysis failed")

    monkeypatch.setattr(
        security_api,
        "get_accessible_repository",
        mock_accessible_repository,
    )
    monkeypatch.setattr(
        security_api,
        "analyze_repository_dependencies",
        mock_analyze_dependencies,
    )
    monkeypatch.setattr(
        security_api,
        "analyze_repository_security",
        mock_analyze_security,
    )

    response = security_api_client.post(
        "/security-analysis/",
        params={"owner": "test-owner", "repo": "test-repo"},
    )

    assert response.status_code == 500

    activities = database.list_activities(user_id=1001)

    assert len(activities) == 1
    assert activities[0]["action_type"] == "security_analysis"
    assert activities[0]["status"] == "failed"
    assert activities[0]["details"]["error_type"] == "RuntimeError"


def test_security_analysis_empty_dependencies_records_failure(
    security_api_client,
    monkeypatch,
):
    async def mock_accessible_repository(*args, **kwargs):
        return {"full_name": "test-owner/test-repo"}

    async def mock_analyze_dependencies(*args, **kwargs):
        return None

    monkeypatch.setattr(
        security_api,
        "get_accessible_repository",
        mock_accessible_repository,
    )
    monkeypatch.setattr(
        security_api,
        "analyze_repository_dependencies",
        mock_analyze_dependencies,
    )

    response = security_api_client.post(
        "/security-analysis/",
        params={"owner": "test-owner", "repo": "test-repo"},
    )

    assert response.status_code == 400

    activities = database.list_activities(user_id=1001)

    assert len(activities) == 1
    assert activities[0]["action_type"] == "security_analysis"
    assert activities[0]["status"] == "failed"
    assert activities[0]["details"]["error_type"] == "HTTPException"


def test_security_analysis_access_denial_creates_no_activity(
    security_api_client,
    monkeypatch,
):
    async def mock_accessible_repository(*args, **kwargs):
        raise HTTPException(
            status_code=403,
            detail="Repository access denied",
        )

    monkeypatch.setattr(
        security_api,
        "get_accessible_repository",
        mock_accessible_repository,
    )

    response = security_api_client.post(
        "/security-analysis/",
        params={"owner": "test-owner", "repo": "test-repo"},
    )

    assert response.status_code == 403
    assert database.list_activities(user_id=1001) == []
