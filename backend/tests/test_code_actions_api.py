
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.api.dependencies import get_current_session
from app.api import code_actions as code_actions_api
from app import database


@pytest.fixture
def code_actions_api_client(tmp_path, monkeypatch):
    monkeypatch.setattr(
        database,
        "DATABASE_PATH",
        tmp_path / "code_actions_api.db",
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


def code_action_payload():
    return {
        "owner": "test-owner",
        "repo": "test-repo",
        "file_path": "src/main.py",
        "code": "def hello():\n    print('Hello')",
        "action": "fix",
    }


def test_code_suggestion_creates_successful_activity(
    code_actions_api_client,
    monkeypatch,
):
    async def mock_accessible_repository(*args, **kwargs):
        return {"full_name": "test-owner/test-repo"}

    async def mock_generate_code_action(*args, **kwargs):
        return "def hello():\n    print('Hello, world!')"

    monkeypatch.setattr(
        code_actions_api,
        "get_accessible_repository",
        mock_accessible_repository,
    )
    monkeypatch.setattr(
        code_actions_api,
        "generate_code_action",
        mock_generate_code_action,
    )

    response = code_actions_api_client.post(
        "/code-actions/",
        json=code_action_payload(),
    )

    assert response.status_code == 200
    assert response.json()["action"] == "fix"
    assert response.json()["modified_code"] == (
        "def hello():\n    print('Hello, world!')"
    )

    activities = database.list_activities(
        user_id=1001,
        owner="test-owner",
        repo="test-repo",
    )

    assert len(activities) == 1
    assert activities[0]["action_type"] == "code_suggestion"
    assert activities[0]["status"] == "success"
    assert activities[0]["details"]["file_path"] == "src/main.py"
    assert activities[0]["details"]["action"] == "fix"


def test_code_suggestion_records_failed_activity(
    code_actions_api_client,
    monkeypatch,
):
    async def mock_accessible_repository(*args, **kwargs):
        return {"full_name": "test-owner/test-repo"}

    async def mock_generate_code_action(*args, **kwargs):
        raise RuntimeError("Code suggestion failed")

    monkeypatch.setattr(
        code_actions_api,
        "get_accessible_repository",
        mock_accessible_repository,
    )
    monkeypatch.setattr(
        code_actions_api,
        "generate_code_action",
        mock_generate_code_action,
    )

    response = code_actions_api_client.post(
        "/code-actions/",
        json=code_action_payload(),
    )

    assert response.status_code == 500

    activities = database.list_activities(user_id=1001)

    assert len(activities) == 1
    assert activities[0]["action_type"] == "code_suggestion"
    assert activities[0]["status"] == "failed"
    assert activities[0]["details"]["error_type"] == "RuntimeError"


def test_code_suggestion_empty_result_records_failure(
    code_actions_api_client,
    monkeypatch,
):
    async def mock_accessible_repository(*args, **kwargs):
        return {"full_name": "test-owner/test-repo"}

    async def mock_generate_code_action(*args, **kwargs):
        return None

    monkeypatch.setattr(
        code_actions_api,
        "get_accessible_repository",
        mock_accessible_repository,
    )
    monkeypatch.setattr(
        code_actions_api,
        "generate_code_action",
        mock_generate_code_action,
    )

    response = code_actions_api_client.post(
        "/code-actions/",
        json=code_action_payload(),
    )

    assert response.status_code == 400

    activities = database.list_activities(user_id=1001)

    assert len(activities) == 1
    assert activities[0]["action_type"] == "code_suggestion"
    assert activities[0]["status"] == "failed"
    assert activities[0]["details"]["error_type"] == "HTTPException"


def test_code_suggestion_access_denial_creates_no_activity(
    code_actions_api_client,
    monkeypatch,
):
    async def mock_accessible_repository(*args, **kwargs):
        raise HTTPException(
            status_code=403,
            detail="Repository access denied",
        )

    monkeypatch.setattr(
        code_actions_api,
        "get_accessible_repository",
        mock_accessible_repository,
    )

    response = code_actions_api_client.post(
        "/code-actions/",
        json=code_action_payload(),
    )

    assert response.status_code == 403
    assert database.list_activities(user_id=1001) == []
