import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.dependencies import get_current_session
from app import database


@pytest.fixture
def preferences_client(tmp_path, monkeypatch):
    monkeypatch.setattr(
        database,
        "DATABASE_PATH",
        tmp_path / "preferences_api.db",
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


def test_get_preferences_returns_empty_object(preferences_client):
    response = preferences_client.get("/preferences/")

    assert response.status_code == 200
    assert response.json()["preferences"] == {}


def test_update_preferences(preferences_client):
    preferences = {
        "theme": "dark",
        "editor": "vscode",
        "notifications": True,
    }

    response = preferences_client.put(
        "/preferences/",
        json={"preferences": preferences},
    )

    assert response.status_code == 200
    assert response.json()["preferences"] == preferences


def test_preferences_persist_after_update(preferences_client):
    preferences = {
        "theme": "dark",
        "font_size": 16,
    }

    preferences_client.put(
        "/preferences/",
        json={"preferences": preferences},
    )

    response = preferences_client.get("/preferences/")

    assert response.status_code == 200
    assert response.json()["preferences"] == preferences


def test_update_preferences_replaces_existing_values(preferences_client):
    preferences_client.put(
        "/preferences/",
        json={"preferences": {"theme": "dark", "font_size": 16}},
    )

    updated = {"theme": "light"}

    response = preferences_client.put(
        "/preferences/",
        json={"preferences": updated},
    )

    assert response.status_code == 200
    assert response.json()["preferences"] == updated


def test_delete_preferences(preferences_client):
    preferences_client.put(
        "/preferences/",
        json={"preferences": {"theme": "dark"}},
    )

    response = preferences_client.delete("/preferences/")

    assert response.status_code == 200
    assert database.get_user_preferences(1001) == {}


def test_delete_missing_preferences_returns_404(preferences_client):
    response = preferences_client.delete("/preferences/")

    assert response.status_code == 404


def test_preferences_are_isolated_between_users(preferences_client):
    database.update_user_preferences(
        2002,
        {"theme": "light"},
    )

    response = preferences_client.get("/preferences/")

    assert response.status_code == 200
    assert response.json()["preferences"] == {}


def test_preferences_must_be_an_object(preferences_client):
    response = preferences_client.put(
        "/preferences/",
        json={"preferences": ["dark", "light"]},
    )

    assert response.status_code == 422