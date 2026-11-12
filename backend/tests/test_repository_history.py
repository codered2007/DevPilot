
import time

import pytest

from app import database


WORKSPACE_101 = "workspace-101"
WORKSPACE_202 = "workspace-202"


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

    workspace_id = f"workspace-{user_id}"

    database.create_workspace(
        workspace_id,
        user_id,
        f"{login} Workspace",
    )

    return workspace_id


def record_open(
    user_id,
    workspace_id,
    owner,
    repo,
    name,
    description="",
):
    database.record_repository_open(
        user_id=user_id,
        workspace_id=workspace_id,
        owner=owner,
        repo=repo,
        name=name,
        description=description,
    )


def get_history(user_id, workspace_id, limit=10):
    return database.get_repository_history(
        user_id=user_id,
        workspace_id=workspace_id,
        limit=limit,
    )


def test_record_repository_open(isolated_database):
    create_user(101, "alice")

    record_open(
        101, WORKSPACE_101,
        "alice", "devpilot", "DevPilot",
        "AI coding assistant",
    )

    history = get_history(101, WORKSPACE_101)

    assert len(history) == 1
    assert history[0]["owner"] == "alice"
    assert history[0]["repo"] == "devpilot"
    assert history[0]["name"] == "DevPilot"
    assert history[0]["description"] == "AI coding assistant"
    assert history[0]["last_opened_at"] > 0


def test_reopening_repository_updates_existing_record(
    isolated_database,
):
    create_user(101, "alice")

    record_open(
        101, WORKSPACE_101,
        "alice", "devpilot", "DevPilot",
    )

    first_timestamp = get_history(
        101, WORKSPACE_101
    )[0]["last_opened_at"]

    time.sleep(0.01)

    record_open(
        101, WORKSPACE_101,
        "alice", "devpilot", "DevPilot Updated",
    )

    history = get_history(101, WORKSPACE_101)

    assert len(history) == 1
    assert history[0]["name"] == "DevPilot Updated"
    assert history[0]["last_opened_at"] > first_timestamp


def test_repository_history_is_user_specific(
    isolated_database,
):
    create_user(101, "alice")
    create_user(202, "bob")

    record_open(
        101, WORKSPACE_101,
        "alice", "project-a", "Project A",
    )

    record_open(
        202, WORKSPACE_202,
        "bob", "project-b", "Project B",
    )

    alice_history = get_history(101, WORKSPACE_101)
    bob_history = get_history(202, WORKSPACE_202)

    assert len(alice_history) == 1
    assert alice_history[0]["repo"] == "project-a"

    assert len(bob_history) == 1
    assert bob_history[0]["repo"] == "project-b"


def test_repository_history_is_ordered_by_last_opened(
    isolated_database,
):
    create_user(101, "alice")

    record_open(
        101, WORKSPACE_101,
        "alice", "project-a", "Project A",
    )

    time.sleep(0.01)

    record_open(
        101, WORKSPACE_101,
        "alice", "project-b", "Project B",
    )

    history = get_history(101, WORKSPACE_101)

    assert history[0]["repo"] == "project-b"
    assert history[1]["repo"] == "project-a"


def test_repository_history_is_case_insensitive(
    isolated_database,
):
    create_user(101, "alice")

    record_open(
        101, WORKSPACE_101,
        "Alice", "DevPilot", "DevPilot",
    )

    record_open(
        101, WORKSPACE_101,
        "alice", "devpilot", "Updated DevPilot",
    )

    history = get_history(101, WORKSPACE_101)

    assert len(history) == 1
    assert history[0]["name"] == "Updated DevPilot"


def test_deleting_user_removes_repository_history(
    isolated_database,
):
    create_user(101, "alice")

    record_open(
        101, WORKSPACE_101,
        "alice", "devpilot", "DevPilot",
    )

    assert database.delete_user(101) is True

    # The workspace is deleted with its owner.
    # Accessing its history must now be rejected.
    with pytest.raises(ValueError, match="Workspace not found"):
        get_history(101, WORKSPACE_101)

    # Verify the repository history was actually deleted.
    with database.get_connection() as connection:
        count = connection.execute(
            """
            SELECT COUNT(*)
            FROM repository_history
            WHERE user_id = ?
            """,
            (101,),
        ).fetchone()[0]

    assert count == 0

def test_history_rejects_invalid_limit(isolated_database):
    create_user(101, "alice")

    with pytest.raises(ValueError):
        get_history(101, WORKSPACE_101, 0)

    with pytest.raises(ValueError):
        get_history(101, WORKSPACE_101, True)


def test_history_rejects_invalid_user_id(isolated_database):
    with pytest.raises(ValueError):
        get_history(True, WORKSPACE_101)


def test_record_rejects_invalid_repository_data(
    isolated_database,
):
    create_user(101, "alice")

    with pytest.raises(ValueError):
        record_open(
            101, WORKSPACE_101,
            "", "devpilot", "DevPilot",
        )

    with pytest.raises(ValueError):
        record_open(
            101, WORKSPACE_101,
            "alice", "devpilot", "",
        )


def test_repository_history_is_workspace_isolated(
    isolated_database,
):
    create_user(101, "alice")

    second_workspace = "workspace-101-second"

    database.create_workspace(
        second_workspace,
        101,
        "Second Workspace",
    )

    record_open(
        101, WORKSPACE_101,
        "alice", "project-a", "Project A",
    )

    record_open(
        101, second_workspace,
        "alice", "project-b", "Project B",
    )

    first_history = get_history(101, WORKSPACE_101)
    second_history = get_history(101, second_workspace)

    assert len(first_history) == 1
    assert first_history[0]["repo"] == "project-a"

    assert len(second_history) == 1
    assert second_history[0]["repo"] == "project-b"



def test_user_cannot_read_another_users_workspace_history(
    isolated_database,
):
    create_user(101, "alice")
    create_user(202, "bob")

    record_open(
        202, WORKSPACE_202,
        "bob", "private-repo", "Private Repository",
    )

    # Alice cannot access Bob's workspace.
    with pytest.raises(ValueError, match="Workspace not found"):
        get_history(101, WORKSPACE_202)

    # Bob can still access his own repository history.
    bob_history = get_history(202, WORKSPACE_202)

    assert len(bob_history) == 1
    assert bob_history[0]["repo"] == "private-repo"

