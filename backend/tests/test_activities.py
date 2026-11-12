
import pytest

from app import database


USER_WORKSPACE = "test-workspace-1001"
OTHER_WORKSPACE = "test-workspace-2002"


@pytest.fixture
def activity_database(tmp_path, monkeypatch):
    monkeypatch.setattr(
        database,
        "DATABASE_PATH",
        tmp_path / "activities.db",
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


def create_test_activity(
    user_id=1001,
    workspace_id=USER_WORKSPACE,
    repo="repo",
    title="Index repository",
    action_type="indexing",
):
    return database.create_activity(
        user_id=user_id,
        workspace_id=workspace_id,
        owner="owner",
        repo=repo,
        action_type=action_type,
        title=title,
    )


def test_create_activity(activity_database):
    activity = create_test_activity(
        title="Repository indexing"
    )

    assert activity["user_id"] == 1001
    assert activity["workspace_id"] == USER_WORKSPACE
    assert activity["action_type"] == "indexing"
    assert activity["status"] == "running"
    assert activity["completed_at"] is None
    assert activity["details"] == {}


def test_complete_activity_success(activity_database):
    activity = create_test_activity()

    completed = database.complete_activity(
        activity["id"],
        1001,
        USER_WORKSPACE,
        "success",
        {"files_indexed": 25},
    )

    assert completed["status"] == "success"
    assert completed["details"]["files_indexed"] == 25
    assert completed["completed_at"] is not None


def test_complete_activity_failure(activity_database):
    activity = create_test_activity(
        action_type="security_analysis",
        title="Security analysis",
    )

    completed = database.complete_activity(
        activity["id"],
        1001,
        USER_WORKSPACE,
        "failed",
        {"error": "Analysis failed"},
    )

    assert completed["status"] == "failed"
    assert completed["details"]["error"] == "Analysis failed"


def test_completed_activity_cannot_be_completed_again(
    activity_database,
):
    activity = create_test_activity()

    database.complete_activity(
        activity["id"], 1001, USER_WORKSPACE, "success"
    )

    assert database.complete_activity(
        activity["id"], 1001, USER_WORKSPACE, "failed"
    ) is None


def test_activity_is_user_isolated(activity_database):
    activity = create_test_activity()

    assert database.get_activity(
        activity["id"], 2002, OTHER_WORKSPACE
    ) is None

    assert database.list_activities(
        2002, OTHER_WORKSPACE
    ) == []


def test_list_activities_filters_by_repository(activity_database):
    create_test_activity(
        repo="repo-one",
        title="First repository",
    )

    create_test_activity(
        repo="repo-two",
        title="Second repository",
    )

    activities = database.list_activities(
        1001,
        USER_WORKSPACE,
        owner="owner",
        repo="repo-one",
    )

    assert len(activities) == 1
    assert activities[0]["repo"] == "repo-one"


def test_list_activities_respects_limit(activity_database):
    for index in range(5):
        create_test_activity(title=f"Activity {index}")

    assert len(
        database.list_activities(
            1001, USER_WORKSPACE, limit=3
        )
    ) == 3


def test_invalid_activity_status_is_rejected(activity_database):
    activity = create_test_activity()

    with pytest.raises(ValueError):
        database.complete_activity(
            activity["id"], 1001, USER_WORKSPACE, "pending"
        )


def test_invalid_activity_limit_is_rejected(activity_database):
    with pytest.raises(ValueError):
        database.list_activities(
            1001, USER_WORKSPACE, limit=0
        )

    with pytest.raises(ValueError):
        database.list_activities(
            1001, USER_WORKSPACE, limit=101
        )


def test_activities_are_isolated_between_workspaces(
    activity_database,
):
    second_workspace = "second-workspace-1001"

    database.create_workspace(
        second_workspace, 1001, "Second Workspace"
    )

    activity = create_test_activity()

    assert len(
        database.list_activities(1001, USER_WORKSPACE)
    ) == 1

    assert database.list_activities(
        1001, second_workspace
    ) == []

    assert database.get_activity(
        activity["id"], 1001, second_workspace
    ) is None

    assert database.complete_activity(
        activity["id"],
        1001,
        second_workspace,
        "success",
    ) is None

    assert database.get_activity(
        activity["id"], 1001, USER_WORKSPACE
    )["status"] == "running"
