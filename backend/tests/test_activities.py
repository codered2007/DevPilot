
import pytest

from app import database


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

    return database


def test_create_activity(activity_database):
    activity = database.create_activity(
        1001,
        "owner",
        "repo",
        "indexing",
        "Repository indexing",
    )

    assert activity["user_id"] == 1001
    assert activity["action_type"] == "indexing"
    assert activity["status"] == "running"
    assert activity["completed_at"] is None
    assert activity["details"] == {}


def test_complete_activity_success(activity_database):
    activity = database.create_activity(
        1001, "owner", "repo", "indexing", "Index repository"
    )

    completed = database.complete_activity(
        activity["id"],
        1001,
        "success",
        {"files_indexed": 25},
    )

    assert completed["status"] == "success"
    assert completed["details"]["files_indexed"] == 25
    assert completed["completed_at"] is not None


def test_complete_activity_failure(activity_database):
    activity = database.create_activity(
        1001, "owner", "repo", "security_analysis", "Security analysis"
    )

    completed = database.complete_activity(
        activity["id"],
        1001,
        "failed",
        {"error": "Analysis failed"},
    )

    assert completed["status"] == "failed"
    assert completed["details"]["error"] == "Analysis failed"


def test_completed_activity_cannot_be_completed_again(activity_database):
    activity = database.create_activity(
        1001, "owner", "repo", "indexing", "Index repository"
    )

    database.complete_activity(
        activity["id"], 1001, "success"
    )

    assert database.complete_activity(
        activity["id"], 1001, "failed"
    ) is None


def test_activity_is_user_isolated(activity_database):
    activity = database.create_activity(
        1001, "owner", "repo", "indexing", "Index repository"
    )

    assert database.get_activity(activity["id"], 2002) is None

    assert database.list_activities(2002) == []


def test_list_activities_filters_by_repository(activity_database):
    database.create_activity(
        1001, "owner", "repo-one", "indexing", "First repository"
    )

    database.create_activity(
        1001, "owner", "repo-two", "indexing", "Second repository"
    )

    activities = database.list_activities(
        1001, owner="owner", repo="repo-one"
    )

    assert len(activities) == 1
    assert activities[0]["repo"] == "repo-one"


def test_list_activities_respects_limit(activity_database):
    for index in range(5):
        database.create_activity(
            1001,
            "owner",
            "repo",
            "indexing",
            f"Activity {index}",
        )

    assert len(database.list_activities(1001, limit=3)) == 3


def test_invalid_activity_status_is_rejected(activity_database):
    activity = database.create_activity(
        1001, "owner", "repo", "indexing", "Index repository"
    )

    with pytest.raises(ValueError):
        database.complete_activity(
            activity["id"], 1001, "pending"
        )


def test_invalid_activity_limit_is_rejected(activity_database):
    with pytest.raises(ValueError):
        database.list_activities(1001, limit=0)

    with pytest.raises(ValueError):
        database.list_activities(1001, limit=101)
