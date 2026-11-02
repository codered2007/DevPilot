
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.dependencies import get_current_session
from app import database


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


def test_list_activities(activity_api_client):
    database.create_activity(
        1001, "owner", "repo", "indexing", "Repository indexing"
    )

    response = activity_api_client.get("/activities/")

    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["activities"][0]["action_type"] == "indexing"


def test_list_activities_filters_by_repository(activity_api_client):
    database.create_activity(
        1001, "owner", "repo-one", "indexing", "First"
    )

    database.create_activity(
        1001, "owner", "repo-two", "indexing", "Second"
    )

    response = activity_api_client.get(
        "/activities/?owner=owner&repo=repo-one"
    )

    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["activities"][0]["repo"] == "repo-one"


def test_list_activities_requires_owner_and_repo_together(
    activity_api_client,
):
    response = activity_api_client.get(
        "/activities/?owner=owner"
    )

    assert response.status_code == 400


def test_get_activity(activity_api_client):
    activity = database.create_activity(
        1001,
        "owner",
        "repo",
        "repository_summary",
        "Repository summary",
        details={
            "file_path": "README.md",
        },
    )

    database.complete_activity(
        activity_id=activity["id"],
        user_id=1001,
        status="success",
        details={
            "summary": "This repository contains a Python application.",
        },
    )

    response = activity_api_client.get(
        f"/activities/{activity['id']}"
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
    activity = database.create_activity(
        2002, "owner", "repo", "indexing", "Private activity"
    )

    response = activity_api_client.get(
        f"/activities/{activity['id']}"
    )

    assert response.status_code == 404


def test_missing_activity_returns_404(activity_api_client):
    response = activity_api_client.get(
        "/activities/nonexistent-id"
    )

    assert response.status_code == 404


def test_activity_limit_validation(activity_api_client):
    response = activity_api_client.get(
        "/activities/?limit=101"
    )

    assert response.status_code == 422
