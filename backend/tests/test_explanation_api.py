
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.api.dependencies import get_current_session
from app.api import explanation as explanation_api
from app import database


@pytest.fixture
def explanation_api_client(tmp_path, monkeypatch):
    monkeypatch.setattr(
        database,
        "DATABASE_PATH",
        tmp_path / "explanation_api.db",
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


def explanation_payload():
    return {
        "owner": "test-owner",
        "repo": "test-repo",
        "file_path": "src/main.py",
        "code": "def hello():\n    print('Hello')",
    }


def test_code_explanation_creates_successful_activity(
    explanation_api_client,
    monkeypatch,
):
    async def mock_accessible_repository(*args, **kwargs):
        return {"full_name": "test-owner/test-repo"}

    async def mock_explain_code(*args, **kwargs):
        return "This function prints Hello."

    monkeypatch.setattr(
        explanation_api,
        "get_accessible_repository",
        mock_accessible_repository,
    )
    monkeypatch.setattr(
        explanation_api,
        "explain_code",
        mock_explain_code,
    )

    response = explanation_api_client.post(
        "/explain/",
        json=explanation_payload(),
    )

    assert response.status_code == 200
    assert response.json()["response"] == "This function prints Hello."

    activities = database.list_activities(
        user_id=1001,
        owner="test-owner",
        repo="test-repo",
    )

    assert len(activities) == 1
    assert activities[0]["action_type"] == "code_explanation"
    assert activities[0]["status"] == "success"
    assert activities[0]["details"]["file_path"] == "src/main.py"


def test_code_explanation_records_failed_activity(
    explanation_api_client,
    monkeypatch,
):
    async def mock_accessible_repository(*args, **kwargs):
        return {"full_name": "test-owner/test-repo"}

    async def mock_explain_code(*args, **kwargs):
        raise RuntimeError("Explanation generation failed")

    monkeypatch.setattr(
        explanation_api,
        "get_accessible_repository",
        mock_accessible_repository,
    )
    monkeypatch.setattr(
        explanation_api,
        "explain_code",
        mock_explain_code,
    )

    response = explanation_api_client.post(
        "/explain/",
        json=explanation_payload(),
    )

    assert response.status_code == 500

    activities = database.list_activities(user_id=1001)

    assert len(activities) == 1
    assert activities[0]["action_type"] == "code_explanation"
    assert activities[0]["status"] == "failed"
    assert activities[0]["details"]["error_type"] == "RuntimeError"


def test_code_explanation_empty_result_records_failure(
    explanation_api_client,
    monkeypatch,
):
    async def mock_accessible_repository(*args, **kwargs):
        return {"full_name": "test-owner/test-repo"}

    async def mock_explain_code(*args, **kwargs):
        return None

    monkeypatch.setattr(
        explanation_api,
        "get_accessible_repository",
        mock_accessible_repository,
    )
    monkeypatch.setattr(
        explanation_api,
        "explain_code",
        mock_explain_code,
    )

    response = explanation_api_client.post(
        "/explain/",
        json=explanation_payload(),
    )

    assert response.status_code == 400

    activities = database.list_activities(user_id=1001)

    assert len(activities) == 1
    assert activities[0]["action_type"] == "code_explanation"
    assert activities[0]["status"] == "failed"
    assert activities[0]["details"]["error_type"] == "HTTPException"


def test_code_explanation_access_denial_creates_no_activity(
    explanation_api_client,
    monkeypatch,
):
    async def mock_accessible_repository(*args, **kwargs):
        raise HTTPException(
            status_code=403,
            detail="Repository access denied",
        )

    monkeypatch.setattr(
        explanation_api,
        "get_accessible_repository",
        mock_accessible_repository,
    )

    response = explanation_api_client.post(
        "/explain/",
        json=explanation_payload(),
    )

    assert response.status_code == 403
    assert database.list_activities(user_id=1001) == []
