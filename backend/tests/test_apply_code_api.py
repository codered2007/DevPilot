
import pytest
from fastapi import HTTPException

from app.main import app
from app.api.dependencies import get_current_session
from app.api import apply_code as apply_code_api
from app import database


@pytest.fixture
def apply_code_api_client(tmp_path, monkeypatch):
    monkeypatch.setattr(
        database,
        "DATABASE_PATH",
        tmp_path / "apply_code_api.db",
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

    from fastapi.testclient import TestClient

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def apply_code_payload():
    return {
        "owner": "test-owner",
        "repo": "test-repo",
        "file_path": "src/example.py",
        "code": "print('updated')",
        "action": "fix",
    }


def test_apply_code_creates_successful_activity(
    apply_code_api_client,
    apply_code_payload,
    monkeypatch,
):
    async def mock_accessible_repository(*args, **kwargs):
        return {"full_name": "test-owner/test-repo"}

    async def mock_get_default_branch(*args, **kwargs):
        return "main"

    async def mock_get_branch_sha(*args, **kwargs):
        return "base-sha"

    async def mock_create_branch(*args, **kwargs):
        return {"ref": "refs/heads/devpilot/test"}

    async def mock_update_file(*args, **kwargs):
        return {
            "branch": "devpilot/test",
            "commit_sha": "commit-sha",
            "commit_url": "https://github.com/test-owner/test-repo/commit/commit-sha",
        }

    monkeypatch.setattr(
        apply_code_api,
        "get_accessible_repository",
        mock_accessible_repository,
    )
    monkeypatch.setattr(
        apply_code_api,
        "get_default_branch",
        mock_get_default_branch,
    )
    monkeypatch.setattr(
        apply_code_api,
        "get_branch_sha",
        mock_get_branch_sha,
    )
    monkeypatch.setattr(
        apply_code_api,
        "create_branch",
        mock_create_branch,
    )
    monkeypatch.setattr(
        apply_code_api,
        "update_file_on_branch",
        mock_update_file,
    )

    response = apply_code_api_client.post(
    "/apply-code/",
    params={"workspace_id": "test-workspace-1001"},
    json=apply_code_payload,
)

    assert response.status_code == 200
    assert response.json()["commit_sha"] == "commit-sha"

    activities = database.list_activities(
    user_id=1001,
    workspace_id="test-workspace-1001",
    owner="test-owner",
    repo="test-repo",
)

    assert len(activities) == 1

    activity = activities[0]

    assert activity["action_type"] == "apply_code"
    assert activity["status"] == "success"
    assert activity["details"]["file_path"] == "src/example.py"
    assert activity["details"]["action"] == "fix"
    assert activity["details"]["branch"] == "devpilot/test"
    assert activity["details"]["base_branch"] == "main"
    assert activity["details"]["commit_sha"] == "commit-sha"
    assert activity["details"]["commit_url"].endswith("/commit-sha")


def test_apply_code_records_failed_activity(
    apply_code_api_client,
    apply_code_payload,
    monkeypatch,
):
    async def mock_accessible_repository(*args, **kwargs):
        return {"full_name": "test-owner/test-repo"}

    async def mock_get_default_branch(*args, **kwargs):
        raise RuntimeError("GitHub operation failed")

    monkeypatch.setattr(
        apply_code_api,
        "get_accessible_repository",
        mock_accessible_repository,
    )
    monkeypatch.setattr(
        apply_code_api,
        "get_default_branch",
        mock_get_default_branch,
    )

    response = apply_code_api_client.post(
    "/apply-code/",
    params={"workspace_id": "test-workspace-1001"},
    json=apply_code_payload,
)

    assert response.status_code == 500

    activities = database.list_activities(
    user_id=1001,
    workspace_id="test-workspace-1001",
    owner="test-owner",
    repo="test-repo",
)

    assert len(activities) == 1
    assert activities[0]["action_type"] == "apply_code"
    assert activities[0]["status"] == "failed"
    assert activities[0]["details"]["error_type"] == "RuntimeError"


def test_apply_code_empty_result_records_failure(
    apply_code_api_client,
    apply_code_payload,
    monkeypatch,
):
    async def mock_accessible_repository(*args, **kwargs):
        return {"full_name": "test-owner/test-repo"}

    async def mock_get_default_branch(*args, **kwargs):
        return None

    monkeypatch.setattr(
        apply_code_api,
        "get_accessible_repository",
        mock_accessible_repository,
    )
    monkeypatch.setattr(
        apply_code_api,
        "get_default_branch",
        mock_get_default_branch,
    )

    response = apply_code_api_client.post(
    "/apply-code/",
    params={"workspace_id": "test-workspace-1001"},
    json=apply_code_payload,
)

    assert response.status_code == 404

    activities = database.list_activities(
    user_id=1001,
    workspace_id="test-workspace-1001",
    owner="test-owner",
    repo="test-repo",
)

    assert len(activities) == 1
    assert activities[0]["status"] == "failed"
    assert activities[0]["details"]["error_type"] == "HTTPException"


def test_apply_code_access_denial_creates_no_activity(
    apply_code_api_client,
    apply_code_payload,
    monkeypatch,
):
    async def mock_accessible_repository(*args, **kwargs):
        raise HTTPException(
            status_code=403,
            detail="Repository access denied",
        )

    monkeypatch.setattr(
        apply_code_api,
        "get_accessible_repository",
        mock_accessible_repository,
    )

    response = apply_code_api_client.post(
    "/apply-code/",
    params={"workspace_id": "test-workspace-1001"},
    json=apply_code_payload,
)

    assert response.status_code == 403

    activities = database.list_activities(
    user_id=1001,
    workspace_id="test-workspace-1001",
)

    assert activities == []
