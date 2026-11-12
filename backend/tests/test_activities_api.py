
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.dependencies import get_current_session
from app import database


USER_WORKSPACE = "test-workspace-1001"
OTHER_WORKSPACE = "test-workspace-2002"


@pytest.fixture
def activity_api_client(tmp_path, monkeypatch):
    monkeypatch.setattr(
        database,
        "DATABASE_PATH",
        tmp_path / "activity_api.db",
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

    database.create_workspace(
        USER_WORKSPACE, 1001, "Test Workspace"
    )

    database.create_workspace(
        OTHER_WORKSPACE, 2002, "Other Workspace"
    )

    app.dependency_overrides[get_current_session] = lambda: {
        "access_token": "test-token",
        "github_user": {
            "id": 1001,
            "login": "test-user",
        },
    }

    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()


def create_test_activity(
    user_id=1001,
    workspace_id=USER_WORKSPACE,
    repo="repo",
    title="Repository indexing",
    action_type="indexing",
    details=None,
):
    return database.create_activity(
        user_id=user_id,
        workspace_id=workspace_id,
        owner="owner",
        repo=repo,
        action_type=action_type,
        title=title,
        details=details,
    )


def test_list_activities(activity_api_client):
    create_test_activity()

    response = activity_api_client.get(
        "/activities/",
        params={"workspace_id": USER_WORKSPACE},
    )

    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert (
        response.json()["activities"][0]["action_type"]
        == "indexing"
    )


def test_list_activities_filters_by_repository(
    activity_api_client,
):
    create_test_activity(
        repo="repo-one",
        title="First",
    )

    create_test_activity(
        repo="repo-two",
        title="Second",
    )

    response = activity_api_client.get(
        "/activities/",
        params={
            "workspace_id": USER_WORKSPACE,
            "owner": "owner",
            "repo": "repo-one",
        },
    )

    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["activities"][0]["repo"] == "repo-one"


def test_list_activities_requires_owner_and_repo_together(
    activity_api_client,
):
    response = activity_api_client.get(
        "/activities/",
        params={
            "workspace_id": USER_WORKSPACE,
            "owner": "owner",
        },
    )

    assert response.status_code == 400


def test_get_activity(activity_api_client):
    activity = create_test_activity(
        action_type="repository_summary",
        title="Repository summary",
        details={
            "file_path": "README.md",
        },
    )

    database.complete_activity(
        activity_id=activity["id"],
        user_id=1001,
        workspace_id=USER_WORKSPACE,
        status="success",
        details={
            "summary": "This repository contains a Python application.",
        },
    )

    response = activity_api_client.get(
        f"/activities/{activity['id']}",
        params={"workspace_id": USER_WORKSPACE},
    )

    assert response.status_code == 200

    returned_activity = response.json()["activity"]

    assert returned_activity["id"] == activity["id"]
    assert returned_activity["status"] == "success"
    assert returned_activity["details"]["file_path"] == "README.md"
    assert returned_activity["details"]["summary"] == (
        "This repository contains a Python application."
    )
    assert returned_activity["completed_at"] is not None


def test_user_cannot_access_another_users_activity(
    activity_api_client,
):
    activity = create_test_activity(
        user_id=2002,
        workspace_id=OTHER_WORKSPACE,
        title="Private activity",
    )

    response = activity_api_client.get(
        f"/activities/{activity['id']}",
        params={"workspace_id": OTHER_WORKSPACE},
    )

    assert response.status_code == 404


def test_missing_activity_returns_404(activity_api_client):
    response = activity_api_client.get(
        "/activities/nonexistent-id",
        params={"workspace_id": USER_WORKSPACE},
    )

    assert response.status_code == 404


def test_activity_limit_validation(activity_api_client):
    response = activity_api_client.get(
        "/activities/",
        params={
            "workspace_id": USER_WORKSPACE,
            "limit": 101,
        },
    )

    assert response.status_code == 422


def test_missing_workspace_id_is_rejected(
    activity_api_client,
):
    response = activity_api_client.get("/activities/")

    assert response.status_code == 422


def test_user_cannot_list_another_users_activities(
    activity_api_client,
):
    create_test_activity(
        user_id=2002,
        workspace_id=OTHER_WORKSPACE,
        title="Private activity",
    )

    response = activity_api_client.get(
        "/activities/",
        params={"workspace_id": OTHER_WORKSPACE},
    )

    assert response.status_code in (403, 404)


def test_activities_are_isolated_between_workspaces(
    activity_api_client,
):
    second_workspace = "second-workspace-1001"

    database.create_workspace(
        second_workspace, 1001, "Second Workspace"
    )

    activity = create_test_activity()

    response = activity_api_client.get(
        "/activities/",
        params={"workspace_id": second_workspace},
    )

    assert response.status_code == 200
    assert response.json()["count"] == 0

    response = activity_api_client.get(
        f"/activities/{activity['id']}",
        params={"workspace_id": second_workspace},
    )

    assert response.status_code == 404

    response = activity_api_client.get(
        f"/activities/{activity['id']}",
        params={"workspace_id": USER_WORKSPACE},
    )

    assert response.status_code == 200
