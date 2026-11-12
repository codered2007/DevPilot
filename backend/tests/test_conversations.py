
import pytest

from app import database


USER_WORKSPACE = "test-workspace-1001"
OTHER_WORKSPACE = "test-workspace-2002"


@pytest.fixture
def conversation_database(tmp_path, monkeypatch):
    monkeypatch.setattr(
        database,
        "DATABASE_PATH",
        tmp_path / "conversations.db",
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

    return database


def create_test_conversation(
    user_id=1001,
    workspace_id=USER_WORKSPACE,
    owner="owner",
    repo="repo",
    title="New conversation",
):
    return database.create_conversation(
        user_id=user_id,
        workspace_id=workspace_id,
        owner=owner,
        repo=repo,
        title=title,
    )


def add_test_message(
    conversation_id,
    role,
    content,
    sources=None,
    user_id=1001,
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


def test_create_conversation(conversation_database):
    conversation = create_test_conversation(
        owner="test-owner",
        repo="test-repo",
    )

    assert conversation["user_id"] == 1001
    assert conversation["workspace_id"] == USER_WORKSPACE
    assert conversation["owner"] == "test-owner"
    assert conversation["repo"] == "test-repo"
    assert conversation["title"] == "New conversation"


def test_list_conversations_is_user_specific(
    conversation_database,
):
    create_test_conversation(title="User conversation")

    assert len(
        database.list_conversations(
            1001, USER_WORKSPACE, "owner", "repo"
        )
    ) == 1

    assert database.list_conversations(
        2002, OTHER_WORKSPACE, "owner", "repo"
    ) == []


def test_add_and_retrieve_messages(conversation_database):
    conversation = create_test_conversation(title="Test chat")

    add_test_message(
        conversation["id"],
        "user",
        "Explain this function",
    )

    add_test_message(
        conversation["id"],
        "assistant",
        "This function processes input.",
        sources=["src/main.py"],
    )

    messages = database.get_conversation_messages(
        conversation["id"], 1001, USER_WORKSPACE
    )

    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["sources"] == ["src/main.py"]


def test_conversation_messages_are_user_isolated(
    conversation_database,
):
    conversation = create_test_conversation(
        title="Private chat"
    )

    assert database.get_conversation_messages(
        conversation["id"], 2002, OTHER_WORKSPACE
    ) is None


def test_delete_conversation_cascades_messages(
    conversation_database,
):
    conversation = create_test_conversation(title="Delete me")

    add_test_message(
        conversation["id"], "user", "Hello"
    )

    assert database.delete_conversation(
        conversation["id"], 1001, USER_WORKSPACE
    ) is True

    assert database.get_conversation_messages(
        conversation["id"], 1001, USER_WORKSPACE
    ) is None


def test_invalid_message_role_is_rejected(
    conversation_database,
):
    conversation = create_test_conversation(title="Test")

    with pytest.raises(ValueError):
        add_test_message(
            conversation["id"], "system", "Invalid role"
        )


def test_invalid_conversation_owner_is_rejected(
    conversation_database,
):
    with pytest.raises(ValueError):
        create_test_conversation(owner="", title="Test")


def test_first_user_message_sets_conversation_title(
    conversation_database,
):
    conversation = create_test_conversation()

    add_test_message(
        conversation["id"],
        "user",
        "Explain how authentication works",
    )

    updated = database.get_conversation(
        conversation["id"], 1001, USER_WORKSPACE
    )

    assert updated["title"] == (
        "Explain how authentication works"
    )


def test_conversation_title_is_truncated(
    conversation_database,
):
    conversation = create_test_conversation()

    message = "A" * 100

    add_test_message(
        conversation["id"], "user", message
    )

    updated = database.get_conversation(
        conversation["id"], 1001, USER_WORKSPACE
    )

    assert len(updated["title"]) == 60
    assert updated["title"].endswith("...")


def test_conversations_are_isolated_between_workspaces(
    conversation_database,
):
    second_workspace = "second-workspace-1001"

    database.create_workspace(
        second_workspace, 1001, "Second Workspace"
    )

    conversation = create_test_conversation()

    assert len(
        database.list_conversations(
            1001, USER_WORKSPACE, "owner", "repo"
        )
    ) == 1

    assert database.list_conversations(
        1001, second_workspace, "owner", "repo"
    ) == []

    assert database.get_conversation(
        conversation["id"], 1001, second_workspace
    ) is None

    assert database.delete_conversation(
        conversation["id"], 1001, second_workspace
    ) is False

    assert database.get_conversation(
        conversation["id"], 1001, USER_WORKSPACE
    ) is not None


def test_conversation_messages_are_workspace_isolated(
    conversation_database,
):
    second_workspace = "second-workspace-1001"

    database.create_workspace(
        second_workspace, 1001, "Second Workspace"
    )

    conversation = create_test_conversation()

    add_test_message(
        conversation["id"],
        "user",
        "Private message",
    )

    assert database.get_conversation_messages(
        conversation["id"], 1001, second_workspace
    ) is None

    with pytest.raises(ValueError):
        add_test_message(
            conversation["id"],
            "assistant",
            "Unauthorized message",
            workspace_id=second_workspace,
        )

    messages = database.get_conversation_messages(
        conversation["id"], 1001, USER_WORKSPACE
    )

    assert len(messages) == 1
    assert messages[0]["content"] == "Private message"
