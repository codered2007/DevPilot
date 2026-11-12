import pytest

from app import database


@pytest.fixture
def workspace_state_db(tmp_path, monkeypatch):
    monkeypatch.setattr(
        database,
        "DATABASE_PATH",
        tmp_path / "workspace_state.db",
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

    database.create_workspace("workspace-1", 1001, "DevPilot")
    database.create_workspace("workspace-2", 2002, "Private Project")

    return database


def test_set_and_get_workspace_state(workspace_state_db):
    database.set_workspace_state(
        "workspace-1",
        1001,
        "active_view",
        {"tab": "security"},
    )

    state = database.get_workspace_state("workspace-1", 1001)

    assert state == {"active_view": {"tab": "security"}}


def test_workspace_state_updates_existing_key(workspace_state_db):
    database.set_workspace_state(
        "workspace-1", 1001, "active_view", {"tab": "summary"}
    )

    database.set_workspace_state(
        "workspace-1", 1001, "active_view", {"tab": "security"}
    )

    state = database.get_workspace_state("workspace-1", 1001)

    assert state == {"active_view": {"tab": "security"}}


def test_workspace_state_isolated_between_users(workspace_state_db):
    database.set_workspace_state(
        "workspace-2", 2002, "active_view", {"tab": "private"}
    )

    assert database.get_workspace_state("workspace-2", 1001) is None
    assert database.get_workspace_state("workspace-1", 1001) == {}


def test_workspace_state_cannot_be_set_by_another_user(workspace_state_db):
    result = database.set_workspace_state(
        "workspace-2", 1001, "active_view", {"tab": "hacked"}
    )

    assert result is None


def test_delete_workspace_state(workspace_state_db):
    database.set_workspace_state(
        "workspace-1", 1001, "active_view", {"tab": "summary"}
    )

    deleted = database.delete_workspace_state(
        "workspace-1", 1001, "active_view"
    )

    assert deleted is True
    assert database.get_workspace_state("workspace-1", 1001) == {}


def test_delete_missing_workspace_state_returns_false(workspace_state_db):
    assert database.delete_workspace_state(
        "workspace-1", 1001, "missing"
    ) is False


def test_invalid_workspace_state_rejected(workspace_state_db):
    with pytest.raises(ValueError):
        database.set_workspace_state(
            "workspace-1", 1001, "", {"tab": "summary"}
        )

    with pytest.raises(ValueError):
        database.set_workspace_state(
            "workspace-1", 1001, "active_view", ["invalid"]
        )


def test_delete_workspace_cascades_state(workspace_state_db):
    database.set_workspace_state(
        "workspace-1", 1001, "active_view", {"tab": "summary"}
    )

    database.delete_workspace("workspace-1", 1001)

    assert database.get_workspace_state("workspace-1", 1001) is None