import time

import pytest

from app import database


@pytest.fixture
def isolated_database(tmp_path, monkeypatch):
    monkeypatch.setattr(
        database,
        "DATABASE_PATH",
        tmp_path / "test_devpilot.db",
    )
    database.initialize_database()


def create_user(user_id, login):
    database.upsert_user({
        "id": user_id,
        "login": login,
    })


def test_record_repository_open(isolated_database):
    create_user(101, "alice")

    database.record_repository_open(
        101, "alice", "devpilot", "DevPilot", "AI coding assistant"
    )

    history = database.get_repository_history(101)

    assert len(history) == 1
    assert history[0]["owner"] == "alice"
    assert history[0]["repo"] == "devpilot"
    assert history[0]["name"] == "DevPilot"
    assert history[0]["description"] == "AI coding assistant"
    assert history[0]["last_opened_at"] > 0


def test_reopening_repository_updates_existing_record(isolated_database):
    create_user(101, "alice")

    database.record_repository_open(
        101, "alice", "devpilot", "DevPilot"
    )

    first_timestamp = database.get_repository_history(101)[0][
        "last_opened_at"
    ]

    time.sleep(0.01)

    database.record_repository_open(
        101, "alice", "devpilot", "DevPilot Updated"
    )

    history = database.get_repository_history(101)

    assert len(history) == 1
    assert history[0]["name"] == "DevPilot Updated"
    assert history[0]["last_opened_at"] > first_timestamp


def test_repository_history_is_user_specific(isolated_database):
    create_user(101, "alice")
    create_user(202, "bob")

    database.record_repository_open(
        101, "alice", "project-a", "Project A"
    )

    database.record_repository_open(
        202, "bob", "project-b", "Project B"
    )

    assert len(database.get_repository_history(101)) == 1
    assert database.get_repository_history(101)[0]["repo"] == "project-a"

    assert len(database.get_repository_history(202)) == 1
    assert database.get_repository_history(202)[0]["repo"] == "project-b"


def test_repository_history_is_ordered_by_last_opened(isolated_database):
    create_user(101, "alice")

    database.record_repository_open(
        101, "alice", "project-a", "Project A"
    )

    time.sleep(0.01)

    database.record_repository_open(
        101, "alice", "project-b", "Project B"
    )

    history = database.get_repository_history(101)

    assert history[0]["repo"] == "project-b"
    assert history[1]["repo"] == "project-a"


def test_repository_history_is_case_insensitive(isolated_database):
    create_user(101, "alice")

    database.record_repository_open(
        101, "Alice", "DevPilot", "DevPilot"
    )

    database.record_repository_open(
        101, "alice", "devpilot", "Updated DevPilot"
    )

    history = database.get_repository_history(101)

    assert len(history) == 1
    assert history[0]["name"] == "Updated DevPilot"


def test_deleting_user_removes_repository_history(isolated_database):
    create_user(101, "alice")

    database.record_repository_open(
        101, "alice", "devpilot", "DevPilot"
    )

    assert database.delete_user(101) is True
    assert database.get_repository_history(101) == []


def test_history_rejects_invalid_limit(isolated_database):
    with pytest.raises(ValueError):
        database.get_repository_history(101, 0)

    with pytest.raises(ValueError):
        database.get_repository_history(101, True)


def test_history_rejects_invalid_user_id(isolated_database):
    with pytest.raises(ValueError):
        database.get_repository_history(True)


def test_record_rejects_invalid_repository_data(isolated_database):
    create_user(101, "alice")

    with pytest.raises(ValueError):
        database.record_repository_open(
            101, "", "devpilot", "DevPilot"
        )

    with pytest.raises(ValueError):
        database.record_repository_open(
            101, "alice", "devpilot", ""
        )