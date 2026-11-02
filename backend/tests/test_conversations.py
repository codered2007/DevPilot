
import pytest

from app import database


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

    return database


def test_create_conversation(conversation_database):
    conversation = database.create_conversation(
        user_id=1001,
        owner="test-owner",
        repo="test-repo",
        title="New conversation",
    )

    assert conversation["user_id"] == 1001
    assert conversation["owner"] == "test-owner"
    assert conversation["repo"] == "test-repo"
    assert conversation["title"] == "New conversation"


def test_list_conversations_is_user_specific(conversation_database):
    database.create_conversation(
        1001, "owner", "repo", "User conversation"
    )

    assert len(database.list_conversations(1001, "owner", "repo")) == 1
    assert database.list_conversations(2002, "owner", "repo") == []


def test_add_and_retrieve_messages(conversation_database):
    conversation = database.create_conversation(
        1001, "owner", "repo", "Test chat"
    )

    database.add_conversation_message(
        conversation["id"],
        "user",
        "Explain this function",
    )

    database.add_conversation_message(
        conversation["id"],
        "assistant",
        "This function processes input.",
        sources=["src/main.py"],
    )

    messages = database.get_conversation_messages(
        conversation["id"], 1001
    )

    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["sources"] == ["src/main.py"]


def test_conversation_messages_are_user_isolated(conversation_database):
    conversation = database.create_conversation(
        1001, "owner", "repo", "Private chat"
    )

    assert database.get_conversation_messages(
        conversation["id"], 2002
    ) is None


def test_delete_conversation_cascades_messages(conversation_database):
    conversation = database.create_conversation(
        1001, "owner", "repo", "Delete me"
    )

    database.add_conversation_message(
        conversation["id"], "user", "Hello"
    )

    assert database.delete_conversation(
        conversation["id"], 1001
    ) is True

    assert database.get_conversation_messages(
        conversation["id"], 1001
    ) is None


def test_invalid_message_role_is_rejected(conversation_database):
    conversation = database.create_conversation(
        1001, "owner", "repo", "Test"
    )

    with pytest.raises(ValueError):
        database.add_conversation_message(
            conversation["id"], "system", "Invalid role"
        )


def test_invalid_conversation_owner_is_rejected(conversation_database):
    with pytest.raises(ValueError):
        database.create_conversation(
            1001, "", "repo", "Test"
        )
def test_first_user_message_sets_conversation_title(conversation_database):
    conversation = database.create_conversation(
        1001, "owner", "repo", "New conversation"
    )

    database.add_conversation_message(
        conversation["id"],
        "user",
        "Explain how authentication works",
    )

    updated = database.get_conversation(
        conversation["id"], 1001
    )

    assert updated["title"] == "Explain how authentication works"

def test_conversation_title_is_truncated(conversation_database):
    conversation = database.create_conversation(
        1001, "owner", "repo", "New conversation"
    )

    message = "A" * 100

    database.add_conversation_message(
        conversation["id"], "user", message
    )

    updated = database.get_conversation(
        conversation["id"], 1001
    )

    assert len(updated["title"]) == 60
    assert updated["title"].endswith("...")