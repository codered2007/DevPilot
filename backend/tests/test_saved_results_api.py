
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.dependencies import get_current_session
from app import database


@pytest.fixture
def saved_results_client(tmp_path, monkeypatch):
    monkeypatch.setattr(
        database,
        "DATABASE_PATH",
        tmp_path / "saved_results_api.db",
    )

    database.initialize_database()

    database.upsert_user({
        "id": 1001,
        "login": "test-user",
        "name": "Test User",
    })

    database.upsert_user({
        "id": 2002,
        "login": "another-user",
        "name": "Another User",
    })

    # Create workspaces belonging to separate users.
    database.create_workspace(
    user_id=1001,
    workspace_id="test-workspace-1001",
    name="Test Workspace",
)

    database.create_workspace(
    user_id=2002,
    workspace_id="test-workspace-2002",
    name="Private Workspace",
)

    app.dependency_overrides[get_current_session] = lambda: {
        "access_token": "test-token",
        "github_user": {
            "id": 1001,
            "login": "test-user",
        },
    }

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


def get_workspace_id(user_id: int) -> str:
    workspaces = database.list_workspaces(user_id=user_id)
    assert workspaces
    return workspaces[0]["id"]


def create_test_result(
    user_id: int = 1001,
    result_type: str = "summary",
    owner: str = "test-user",
    repo: str = "devpilot",
):
    return database.save_result(
        user_id=user_id,
        workspace_id=get_workspace_id(user_id),
        owner=owner,
        repo=repo,
        result_type=result_type,
        title=f"{result_type.title()} Result",
        content={"text": "Saved"},
    )


def test_create_saved_result(saved_results_client):
    workspace_id = get_workspace_id(1001)

    response = saved_results_client.post(
        "/saved-results/",
        json={
            "workspace_id": workspace_id,
            "owner": "test-user",
            "repo": "devpilot",
            "result_type": "summary",
            "title": "Repository Summary",
            "content": {"overview": "FastAPI project"},
        },
    )

    assert response.status_code == 201
    result = response.json()["saved_result"]
    assert result["workspace_id"] == workspace_id
    assert result["title"] == "Repository Summary"
    assert result["content"]["overview"] == "FastAPI project"


def test_list_saved_results(saved_results_client):
    workspace_id = get_workspace_id(1001)
    create_test_result()

    response = saved_results_client.get(
        "/saved-results/",
        params={"workspace_id": workspace_id},
    )

    assert response.status_code == 200
    assert response.json()["count"] == 1


def test_filter_saved_results(saved_results_client):
    workspace_id = get_workspace_id(1001)

    create_test_result(result_type="summary")
    create_test_result(result_type="security")

    response = saved_results_client.get(
        "/saved-results/",
        params={
            "workspace_id": workspace_id,
            "owner": "test-user",
            "repo": "devpilot",
            "result_type": "security",
        },
    )

    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert (
        response.json()["saved_results"][0]["result_type"]
        == "security"
    )


def test_get_saved_result(saved_results_client):
    workspace_id = get_workspace_id(1001)
    saved = create_test_result()

    response = saved_results_client.get(
        f"/saved-results/{saved['id']}",
        params={"workspace_id": workspace_id},
    )

    assert response.status_code == 200
    assert response.json()["saved_result"]["id"] == saved["id"]


def test_delete_saved_result(saved_results_client):
    workspace_id = get_workspace_id(1001)
    saved = create_test_result()

    response = saved_results_client.delete(
        f"/saved-results/{saved['id']}",
        params={"workspace_id": workspace_id},
    )

    assert response.status_code == 200
    assert (
        database.get_saved_result(
            result_id=saved["id"],
            user_id=1001,
            workspace_id=workspace_id,
        )
        is None
    )


def test_user_cannot_access_another_users_result(
    saved_results_client,
):
    other_workspace_id = get_workspace_id(2002)

    saved = create_test_result(
        user_id=2002,
        owner="another-user",
        repo="private-repo",
    )

    response = saved_results_client.get(
        f"/saved-results/{saved['id']}",
        params={"workspace_id": other_workspace_id},
    )

    assert response.status_code == 404


def test_invalid_result_type_is_rejected(saved_results_client):
    response = saved_results_client.post(
        "/saved-results/",
        json={
            "workspace_id": get_workspace_id(1001),
            "owner": "test-user",
            "repo": "devpilot",
            "result_type": "invalid",
            "title": "Invalid",
            "content": {},
        },
    )

    assert response.status_code == 422


def test_list_requires_owner_and_repo_together(
    saved_results_client,
):
    response = saved_results_client.get(
        "/saved-results/",
        params={
            "workspace_id": get_workspace_id(1001),
            "owner": "test-user",
        },
    )

    assert response.status_code == 400


def test_missing_workspace_id_is_rejected(
    saved_results_client,
):
    response = saved_results_client.get("/saved-results/")

    assert response.status_code == 422


def test_user_cannot_save_to_another_users_workspace(
    saved_results_client,
):
    response = saved_results_client.post(
        "/saved-results/",
        json={
            "workspace_id": get_workspace_id(2002),
            "owner": "test-user",
            "repo": "devpilot",
            "result_type": "summary",
            "title": "Unauthorized",
            "content": {},
        },
    )

    assert response.status_code == 404


def test_user_cannot_delete_another_users_result(
    saved_results_client,
):
    saved = create_test_result(
        user_id=2002,
        owner="another-user",
        repo="private-repo",
    )

    response = saved_results_client.delete(
        f"/saved-results/{saved['id']}",
        params={"workspace_id": get_workspace_id(2002)},
    )

    assert response.status_code == 404

    assert (
        database.get_saved_result(
            result_id=saved["id"],
            user_id=2002,
            workspace_id=get_workspace_id(2002),
        )
        is not None
    )
