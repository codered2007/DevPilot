
from fastapi.testclient import TestClient

from app.api.dependencies import get_current_session
from app.main import app
from app import database
from pathlib import Path


client = TestClient(app)


def setup_user_database(monkeypatch, tmp_path):
    monkeypatch.setattr(
        database,
        "DATABASE_PATH",
        tmp_path / "test.db",
    )

    database.initialize_database()

    database.upsert_user({
        "id": 101,
        "login": "alice",
    })

    database.upsert_user({
        "id": 202,
        "login": "bob",
    })


def mock_repository_access(monkeypatch):
    async def fake_access(owner, repo, token):
        return {
            "owner": {"login": owner},
            "name": repo,
            "full_name": f"{owner}/{repo}",
        }

    monkeypatch.setattr(
        "app.api.chat.get_accessible_repository",
        fake_access,
    )


def authenticate(user_id=101):
    app.dependency_overrides[get_current_session] = lambda: {
        "github_user": {
            "id": user_id,
            "login": "alice" if user_id == 101 else "bob",
        },
        "access_token": "test-token",
    }


def cleanup_authentication():
    app.dependency_overrides.pop(
        get_current_session,
        None,
    )


def test_chat_conversations_require_authentication():
    response = client.get(
        "/chat/conversations",
        params={"owner": "owner", "repo": "repo"},
    )

    assert response.status_code == 401


def test_create_and_list_conversations(monkeypatch, tmp_path):
    setup_user_database(monkeypatch, tmp_path)
    mock_repository_access(monkeypatch)
    authenticate()

    try:
        created = client.post(
            "/chat/conversations",
            params={"owner": "owner", "repo": "repo"},
        )

        assert created.status_code == 200

        conversation = created.json()["conversation"]

        assert conversation["user_id"] == 101
        assert conversation["owner"] == "owner"
        assert conversation["repo"] == "repo"

        listed = client.get(
            "/chat/conversations",
            params={"owner": "owner", "repo": "repo"},
        )

        assert listed.status_code == 200

        conversations = listed.json()["conversations"]

        assert len(conversations) == 1
        assert conversations[0]["id"] == conversation["id"]

    finally:
        cleanup_authentication()


def test_user_cannot_access_another_users_conversation(
    monkeypatch,
    tmp_path,
):
    setup_user_database(monkeypatch, tmp_path)

    conversation = database.create_conversation(
        202,
        "owner",
        "repo",
        "Bob's private chat",
    )

    mock_repository_access(monkeypatch)
    authenticate(101)

    try:
        response = client.get(
            f"/chat/conversations/{conversation['id']}",
            params={"owner": "owner", "repo": "repo"},
        )

        assert response.status_code == 404

    finally:
        cleanup_authentication()


def test_conversation_messages_can_be_restored(
    monkeypatch,
    tmp_path,
):
    setup_user_database(monkeypatch, tmp_path)

    conversation = database.create_conversation(
        101,
        "owner",
        "repo",
    )

    database.add_conversation_message(
        conversation["id"],
        "user",
        "Explain this repository",
    )

    database.add_conversation_message(
        conversation["id"],
        "assistant",
        "This is a test response.",
        sources=["main.py"],
    )

    mock_repository_access(monkeypatch)
    authenticate()

    try:
        response = client.get(
            f"/chat/conversations/{conversation['id']}",
            params={"owner": "owner", "repo": "repo"},
        )

        assert response.status_code == 200

        messages = response.json()["messages"]

        assert len(messages) == 2
        assert messages[0]["content"] == "Explain this repository"
        assert messages[1]["content"] == "This is a test response."
        assert messages[1]["sources"] == ["main.py"]

    finally:
        cleanup_authentication()


def test_user_can_delete_own_conversation(
    monkeypatch,
    tmp_path,
):
    setup_user_database(monkeypatch, tmp_path)

    conversation = database.create_conversation(
        101,
        "owner",
        "repo",
    )

    database.add_conversation_message(
        conversation["id"],
        "user",
        "Hello",
    )

    mock_repository_access(monkeypatch)
    authenticate()

    try:
        response = client.delete(
            f"/chat/conversations/{conversation['id']}",
            params={"owner": "owner", "repo": "repo"},
        )

        assert response.status_code == 200

        assert database.get_conversation(
            conversation["id"],
            101,
        ) is None

    finally:
        cleanup_authentication()


def test_conversation_cannot_be_used_with_another_repository(
    monkeypatch,
    tmp_path,
):
    setup_user_database(monkeypatch, tmp_path)

    conversation = database.create_conversation(
        101,
        "owner",
        "repo",
    )

    mock_repository_access(monkeypatch)
    authenticate()

    try:
        response = client.get(
            f"/chat/conversations/{conversation['id']}",
            params={
                "owner": "owner",
                "repo": "another-repo",
            },
        )

        assert response.status_code == 404

    finally:
        cleanup_authentication()
