
from fastapi.testclient import TestClient

from app.api.dependencies import get_current_session
from app.main import app


client = TestClient(app)


def test_list_workspaces_requires_authentication():
    response = client.get("/workspaces")
    assert response.status_code == 401


def test_create_workspace_requires_authentication():
    response = client.post(
        "/workspaces",
        json={"name": "My workspace"},
    )
    assert response.status_code == 401


def test_delete_workspace_requires_authentication():
    response = client.delete("/workspaces/workspace-123")
    assert response.status_code == 401


def test_user_can_create_and_list_own_workspace(monkeypatch):
    from app import database

    fake_session = {
        "github_user": {"id": 101, "login": "alice"},
        "access_token": "test-token",
    }
    monkeypatch.setattr(
        database,
        "DATABASE_PATH",
        __import__("pathlib").Path(
            __import__("tempfile").mkdtemp()
        ) / "test.db",
    )
    database.initialize_database()
    database.upsert_user(
        {"id": 101, "login": "alice"}
    )

    app.dependency_overrides[get_current_session] = lambda: fake_session
    try:
        created = client.post(
            "/workspaces",
            json={"name": "Alice's workspace"},
        )
        assert created.status_code == 201
        workspace = created.json()["workspace"]
        assert workspace["user_id"] == 101
        assert workspace["name"] == "Alice's workspace"

        listed = client.get("/workspaces")
        assert listed.status_code == 200
        assert [w["id"] for w in listed.json()["workspaces"]] == [
            workspace["id"]
        ]
    finally:
        app.dependency_overrides.pop(get_current_session, None)


def test_user_cannot_delete_another_users_workspace(monkeypatch, tmp_path):
    from app import database
    from pathlib import Path

    monkeypatch.setattr(
        database,
        "DATABASE_PATH",
        tmp_path / "test.db",
    )
    database.initialize_database()
    database.upsert_user({"id": 101, "login": "alice"})
    database.upsert_user({"id": 202, "login": "bob"})
    database.create_workspace("bob-workspace", 202, "Bob's workspace")

    app.dependency_overrides[get_current_session] = lambda: {
        "github_user": {"id": 101, "login": "alice"},
        "access_token": "test-token",
    }
    try:
        response = client.delete("/workspaces/bob-workspace")
        assert response.status_code == 404
        assert len(database.list_workspaces(202)) == 1
    finally:
        app.dependency_overrides.pop(get_current_session, None)


def test_blank_workspace_name_is_rejected(monkeypatch):
    app.dependency_overrides[get_current_session] = lambda: {
        "github_user": {"id": 101, "login": "alice"},
        "access_token": "test-token",
    }
    try:
        response = client.post(
            "/workspaces",
            json={"name": "   "},
        )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.pop(get_current_session, None)
