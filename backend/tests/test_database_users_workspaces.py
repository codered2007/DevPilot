
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


def github_user(user_id, login, name=None):
    return {
        "id": user_id,
        "login": login,
        "name": name,
        "avatar_url": None,
        "email": None,
    }


def test_user_is_persisted(isolated_database):
    database.upsert_user(github_user(101, "alice", "Alice"))

    with database.get_connection() as connection:
        row = connection.execute(
            "SELECT github_id, login, name FROM users WHERE github_id = ?",
            (101,),
        ).fetchone()

    assert row["github_id"] == 101
    assert row["login"] == "alice"
    assert row["name"] == "Alice"


def test_repeated_login_updates_existing_user(isolated_database):
    database.upsert_user(github_user(101, "alice", "Alice"))
    database.upsert_user(github_user(101, "alice-new", "Alice Updated"))

    with database.get_connection() as connection:
        rows = connection.execute(
            "SELECT github_id, login, name FROM users"
        ).fetchall()

    assert len(rows) == 1
    assert rows[0]["github_id"] == 101
    assert rows[0]["login"] == "alice-new"
    assert rows[0]["name"] == "Alice Updated"


def test_workspace_requires_existing_user(isolated_database):
    with pytest.raises(Exception):
        database.create_workspace("workspace-1", 999, "Private workspace")


def test_users_only_list_their_own_workspaces(isolated_database):
    database.upsert_user(github_user(101, "alice"))
    database.upsert_user(github_user(202, "bob"))

    database.create_workspace("alice-ws", 101, "Alice workspace")
    database.create_workspace("bob-ws", 202, "Bob workspace")

    assert [w["id"] for w in database.list_workspaces(101)] == ["alice-ws"]
    assert [w["id"] for w in database.list_workspaces(202)] == ["bob-ws"]


def test_user_cannot_delete_another_users_workspace(isolated_database):
    database.upsert_user(github_user(101, "alice"))
    database.upsert_user(github_user(202, "bob"))
    database.create_workspace("bob-ws", 202, "Bob workspace")

    deleted = database.delete_workspace("bob-ws", 101)

    assert deleted is False
    assert [w["id"] for w in database.list_workspaces(202)] == ["bob-ws"]


def test_user_can_delete_own_workspace(isolated_database):
    database.upsert_user(github_user(101, "alice"))
    database.create_workspace("alice-ws", 101, "Alice workspace")

    assert database.delete_workspace("alice-ws", 101) is True
    assert database.list_workspaces(101) == []


def test_invalid_github_identity_is_rejected(isolated_database):
    with pytest.raises(ValueError):
        database.upsert_user({"id": True, "login": "invalid"})

    with pytest.raises(ValueError):
        database.upsert_user({"id": 101, "login": "  "})


def test_reinitialization_preserves_existing_records(isolated_database):
    database.upsert_user(github_user(101, "alice"))
    database.create_workspace("alice-ws", 101, "Alice workspace")

    database.initialize_database()

    assert len(database.list_workspaces(101)) == 1

def test_delete_user_removes_account_and_workspaces(isolated_database):
    database.upsert_user(github_user(101, "alice"))
    database.create_workspace("alice-ws", 101, "Alice workspace")

    assert database.delete_user(101) is True
    assert database.list_workspaces(101) == []

    with database.get_connection() as connection:
        user = connection.execute(
            "SELECT github_id FROM users WHERE github_id = ?",
            (101,),
        ).fetchone()

    assert user is None


def test_delete_user_preserves_other_users(isolated_database):
    database.upsert_user(github_user(101, "alice"))
    database.upsert_user(github_user(202, "bob"))
    database.create_workspace("alice-ws", 101, "Alice workspace")
    database.create_workspace("bob-ws", 202, "Bob workspace")

    assert database.delete_user(101) is True

    assert database.list_workspaces(101) == []
    assert [w["id"] for w in database.list_workspaces(202)] == ["bob-ws"]

    with database.get_connection() as connection:
        bob = connection.execute(
            "SELECT github_id FROM users WHERE github_id = ?",
            (202,),
        ).fetchone()

    assert bob is not None


def test_delete_missing_user_returns_false(isolated_database):
    assert database.delete_user(999) is False

def test_delete_user_removes_their_sessions(isolated_database):
    database.upsert_user(github_user(101, "alice"))
    database.upsert_user(github_user(202, "bob"))

    database.save_session(
        "alice-session",
        {"github_user": {"id": 101}, "expires_at": 9999999999},
    )
    database.save_session(
        "bob-session",
        {"github_user": {"id": 202}, "expires_at": 9999999999},
    )

    assert database.delete_user(101) is True
    assert database.get_session("alice-session") is None
    assert database.get_session("bob-session") is not None
def test_delete_user_removes_only_their_repository_indexes(isolated_database):
    database.upsert_user(github_user(101, "alice"))
    database.upsert_user(github_user(202, "bob"))

    with database.get_connection() as connection:
        connection.execute(
            """
            INSERT INTO repository_indexes
                (user_id, owner, repo, collection_name, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (101, "alice", "repo-a", "collection-a", 1.0),
        )
        connection.execute(
            """
            INSERT INTO repository_indexes
                (user_id, owner, repo, collection_name, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (202, "bob", "repo-b", "collection-b", 1.0),
        )

    assert database.delete_user(101) is True

    with database.get_connection() as connection:
        rows = connection.execute(
            "SELECT user_id, collection_name FROM repository_indexes"
        ).fetchall()

    assert [(row["user_id"], row["collection_name"]) for row in rows] == [
        (202, "collection-b")
    ]


def test_delete_user_queues_chroma_collections(database):
    from app.database import (
        get_connection,
        upsert_user,
        delete_user,
    )

    upsert_user({"id": 101, "login": "user-one"})
    upsert_user({"id": 202, "login": "user-two"})

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO repository_indexes
                (user_id, owner, repo, collection_name, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (101, "owner", "repo", "collection-user-one", 1000),
        )
        connection.execute(
            """
            INSERT INTO repository_indexes
                (user_id, owner, repo, collection_name, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (202, "owner", "repo", "collection-user-two", 1000),
        )

    assert delete_user(101) is True

    with get_connection() as connection:
        queued = connection.execute(
            "SELECT collection_name, user_id FROM chroma_cleanup_queue"
        ).fetchall()

    assert len(queued) == 1
    assert dict(queued[0]) == {
        "collection_name": "collection-user-one",
        "user_id": 101,
    }


def test_delete_user_without_indexes_creates_no_cleanup_entries(database):
    from app.database import (
        get_connection,
        upsert_user,
        delete_user,
    )

    upsert_user({"id": 303, "login": "user-three"})

    assert delete_user(303) is True

    with get_connection() as connection:
        queued_count = connection.execute(
            "SELECT COUNT(*) FROM chroma_cleanup_queue"
        ).fetchone()[0]

    assert queued_count == 0




def test_delete_user_queues_chroma_collections(isolated_database):
    database.upsert_user(github_user(101, "alice"))
    database.upsert_user(github_user(202, "bob"))

    with database.get_connection() as connection:
        connection.execute(
            """
            INSERT INTO repository_indexes
                (user_id, owner, repo, collection_name, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (101, "owner", "repo", "collection-alice", 1000),
        )
        connection.execute(
            """
            INSERT INTO repository_indexes
                (user_id, owner, repo, collection_name, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (202, "owner", "repo", "collection-bob", 1000),
        )

    assert database.delete_user(101) is True

    with database.get_connection() as connection:
        queued = connection.execute(
            "SELECT collection_name, user_id FROM chroma_cleanup_queue"
        ).fetchall()

    assert len(queued) == 1
    assert dict(queued[0]) == {
        "collection_name": "collection-alice",
        "user_id": 101,
    }


def test_delete_user_without_indexes_creates_no_cleanup_entries(
    isolated_database,
):
    database.upsert_user(github_user(303, "charlie"))

    assert database.delete_user(303) is True

    with database.get_connection() as connection:
        queued_count = connection.execute(
            "SELECT COUNT(*) FROM chroma_cleanup_queue"
        ).fetchone()[0]

    assert queued_count == 0



def test_chroma_cleanup_queue_lifecycle(isolated_database):
    database.upsert_user(github_user(404, "cleanup-user"))

    with database.get_connection() as connection:
        connection.execute(
            """
            INSERT INTO repository_indexes
                (user_id, owner, repo, collection_name, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (404, "owner", "repo", "cleanup-test-collection", 1000),
        )

    assert database.delete_user(404) is True

    pending = database.get_pending_chroma_cleanup()

    assert len(pending) == 1
    assert pending[0]["collection_name"] == "cleanup-test-collection"
    assert pending[0]["attempts"] == 0

    assert database.fail_chroma_cleanup(
        "cleanup-test-collection",
        "Simulated deletion failure",
    ) is True

    pending = database.get_pending_chroma_cleanup()

    assert pending[0]["attempts"] == 1
    assert pending[0]["last_error"] == "Simulated deletion failure"

    assert database.complete_chroma_cleanup(
        "cleanup-test-collection"
    ) is True

    assert database.get_pending_chroma_cleanup() == []


def test_cleanup_queue_rejects_invalid_limit(isolated_database):
    with pytest.raises(ValueError):
        database.get_pending_chroma_cleanup(0)

    with pytest.raises(ValueError):
        database.get_pending_chroma_cleanup(True)


def test_cleanup_failure_rejects_empty_error(isolated_database):
    with pytest.raises(ValueError):
        database.fail_chroma_cleanup("some-collection", "")