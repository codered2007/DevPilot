
import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_current_session
from app.main import app
from app import database


USER_WORKSPACE = "test-workspace-101"
OTHER_WORKSPACE = "test-workspace-202"

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

    database.create_workspace(
        USER_WORKSPACE, 101, "Alice Workspace"
    )

    database.create_workspace(
        OTHER_WORKSPACE, 202, "Bob Workspace"
    )


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


def conversation_params(
    workspace_id=USER_WORKSPACE,
    repo="repo",
):
    return {
        "workspace_id": workspace_id,
        "owner": "owner",
        "repo": repo,
    }


def create_test_conversation(
    user_id=101,
    workspace_id=USER_WORKSPACE,
    repo="repo",
    title="New conversation",
):
    return database.create_conversation(
        user_id=user_id,
        workspace_id=workspace_id,
        owner="owner",
        repo=repo,
        title=title,
    )


def add_test_message(
    conversation_id,
    role,
    content,
    sources=None,
    user_id=101,
    workspace_id=USER_WORKSPACE,
):
    return database.add_conversation_message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        sources=sources,
        user_id=user_id,
        workspace_id=workspace_id,
    )


def test_chat_conversations_require_authentication():
    cleanup_authentication()

    response = client.get(
        "/chat/conversations",
        params=conversation_params(),
    )

    assert response.status_code == 401


def test_create_and_list_conversations(monkeypatch, tmp_path):
    setup_user_database(monkeypatch, tmp_path)
    mock_repository_access(monkeypatch)
    authenticate()

    try:
        created = client.post(
            "/chat/conversations",
            params=conversation_params(),
        )

        assert created.status_code == 200

        conversation = created.json()["conversation"]

        assert conversation["user_id"] == 101
        assert conversation["workspace_id"] == USER_WORKSPACE
        assert conversation["owner"] == "owner"
        assert conversation["repo"] == "repo"

        listed = client.get(
            "/chat/conversations",
            params=conversation_params(),
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

    conversation = create_test_conversation(
        user_id=202,
        workspace_id=OTHER_WORKSPACE,
        title="Bob's private chat",
    )

    mock_repository_access(monkeypatch)
    authenticate(101)

    try:
        response = client.get(
            f"/chat/conversations/{conversation['id']}",
            params=conversation_params(OTHER_WORKSPACE),
        )

        assert response.status_code == 404

    finally:
        cleanup_authentication()


def test_conversation_messages_can_be_restored(
    monkeypatch,
    tmp_path,
):
    setup_user_database(monkeypatch, tmp_path)

    conversation = create_test_conversation()

    add_test_message(
        conversation["id"],
        "user",
        "Explain this repository",
    )

    add_test_message(
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
            params=conversation_params(),
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

    conversation = create_test_conversation()

    add_test_message(
        conversation["id"],
        "user",
        "Hello",
    )

    mock_repository_access(monkeypatch)
    authenticate()

    try:
        response = client.delete(
            f"/chat/conversations/{conversation['id']}",
            params=conversation_params(),
        )

        assert response.status_code == 200

        assert database.get_conversation(
            conversation["id"],
            101,
            USER_WORKSPACE,
        ) is None

    finally:
        cleanup_authentication()


def test_conversation_cannot_be_used_with_another_repository(
    monkeypatch,
    tmp_path,
):
    setup_user_database(monkeypatch, tmp_path)

    conversation = create_test_conversation()

    mock_repository_access(monkeypatch)
    authenticate()

    try:
        response = client.get(
            f"/chat/conversations/{conversation['id']}",
            params=conversation_params(repo="another-repo"),
        )

        assert response.status_code == 404

    finally:
        cleanup_authentication()


def test_conversation_cannot_be_accessed_from_another_workspace(
    monkeypatch,
    tmp_path,
):
    setup_user_database(monkeypatch, tmp_path)

    second_workspace = "second-workspace-101"

    database.create_workspace(
        second_workspace, 101, "Second Workspace"
    )

    conversation = create_test_conversation()

    mock_repository_access(monkeypatch)
    authenticate()

    try:
        response = client.get(
            f"/chat/conversations/{conversation['id']}",
            params=conversation_params(second_workspace),
        )

        assert response.status_code == 404

        response = client.delete(
            f"/chat/conversations/{conversation['id']}",
            params=conversation_params(second_workspace),
        )

        assert response.status_code == 404

        assert database.get_conversation(
            conversation["id"], 101, USER_WORKSPACE
        ) is not None

    finally:
        cleanup_authentication()


def test_chat_conversations_require_workspace_id(
    monkeypatch,
    tmp_path,
):
    setup_user_database(monkeypatch, tmp_path)
    mock_repository_access(monkeypatch)
    authenticate()

    try:
        response = client.get(
            "/chat/conversations",
            params={
                "owner": "owner",
                "repo": "repo",
            },
        )

        assert response.status_code == 422

    finally:
        cleanup_authentication()
