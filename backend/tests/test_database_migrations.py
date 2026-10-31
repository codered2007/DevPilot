
import sqlite3

from app import database


def test_initialize_database_preserves_existing_data(tmp_path, monkeypatch):
    db_path = tmp_path / "existing.db"
    monkeypatch.setattr(database, "DATABASE_PATH", db_path)

    # Simulate a database created by the earlier version.
    with sqlite3.connect(db_path) as connection:
        connection.execute("""
            CREATE TABLE sessions (
                session_id TEXT PRIMARY KEY,
                session_data TEXT NOT NULL,
                expires_at REAL NOT NULL
            )
        """)
        connection.execute("""
            CREATE TABLE repository_indexes (
                user_id INTEGER NOT NULL,
                owner TEXT NOT NULL,
                repo TEXT NOT NULL,
                collection_name TEXT NOT NULL,
                updated_at REAL NOT NULL,
                PRIMARY KEY (user_id, owner, repo)
            )
        """)
        connection.execute(
            "INSERT INTO sessions VALUES (?, ?, ?)",
            ("session-1", '{"github_user":{"id":101}}', 9999999999),
        )
        connection.execute(
            "INSERT INTO repository_indexes VALUES (?, ?, ?, ?, ?)",
            (101, "alice", "repo", "collection-1", 123.0),
        )

    database.initialize_database()

    with database.get_connection() as connection:
        session = connection.execute(
            "SELECT session_id FROM sessions"
        ).fetchall()
        indexes = connection.execute(
            "SELECT user_id, owner, repo FROM repository_indexes"
        ).fetchall()

    assert len(session) == 1
    assert session[0]["session_id"] == "session-1"
    assert len(indexes) == 1
    assert tuple(indexes[0]) == (101, "alice", "repo")



def test_initialize_database_is_repeatable(tmp_path, monkeypatch):
    monkeypatch.setattr(
        database,
        "DATABASE_PATH",
        tmp_path / "repeatable.db",
    )

    database.initialize_database()
    database.initialize_database()

    with database.get_connection() as connection:
        version = connection.execute(
            "SELECT version FROM schema_version"
        ).fetchone()

    assert version is not None
    assert version["version"] == database.SCHEMA_VERSION
    assert database.SCHEMA_VERSION == 3

def test_initialize_database_rejects_future_schema_version(
    tmp_path, monkeypatch
):
    db_path = tmp_path / "future_version.db"
    monkeypatch.setattr(database, "DATABASE_PATH", db_path)

    with sqlite3.connect(db_path) as connection:
        connection.execute(
            "CREATE TABLE schema_version (version INTEGER NOT NULL)"
        )
        connection.execute(
            "INSERT INTO schema_version (version) VALUES (?)",
            (database.SCHEMA_VERSION + 1,),
        )

    import pytest

    with pytest.raises(RuntimeError, match="newer than supported"):
        database.initialize_database()

def test_future_schema_version_does_not_create_other_tables(
    tmp_path, monkeypatch
):
    db_path = tmp_path / "future_version.db"
    monkeypatch.setattr(database, "DATABASE_PATH", db_path)

    with sqlite3.connect(db_path) as connection:
        connection.execute(
            "CREATE TABLE schema_version (version INTEGER NOT NULL)"
        )
        connection.execute(
            "INSERT INTO schema_version (version) VALUES (?)",
            (database.SCHEMA_VERSION + 1,),
        )

    import pytest

    with pytest.raises(RuntimeError, match="newer than supported"):
        database.initialize_database()

    with sqlite3.connect(db_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }

    assert tables == {"schema_version"}

def test_empty_schema_version_table_is_initialized(
    tmp_path, monkeypatch
):
    db_path = tmp_path / "empty_version.db"
    monkeypatch.setattr(database, "DATABASE_PATH", db_path)

    with sqlite3.connect(db_path) as connection:
        connection.execute(
            "CREATE TABLE schema_version (version INTEGER NOT NULL)"
        )
        connection.execute(
            """
            CREATE TABLE sessions (
                session_id TEXT PRIMARY KEY,
                session_data TEXT NOT NULL,
                expires_at REAL NOT NULL
            )
            """
        )
        connection.execute(
            "INSERT INTO sessions VALUES (?, ?, ?)",
            ("preserve-me", "{}", 9999999999),
        )

    database.initialize_database()

    with database.get_connection() as connection:
        versions = connection.execute(
            "SELECT version FROM schema_version"
        ).fetchall()
        session = connection.execute(
            "SELECT session_id FROM sessions"
        ).fetchone()

    assert [row["version"] for row in versions] == [
        database.SCHEMA_VERSION
    ]
    assert session["session_id"] == "preserve-me"

def test_failed_migration_rolls_back_schema_changes(
    tmp_path, monkeypatch
):
    db_path = tmp_path / "rollback.db"
    monkeypatch.setattr(database, "DATABASE_PATH", db_path)

    with sqlite3.connect(db_path) as connection:
        connection.execute(
            "CREATE TABLE schema_version (version INTEGER NOT NULL)"
        )
        connection.execute(
            "INSERT INTO schema_version (version) VALUES (1)"
        )

    import pytest

    with pytest.raises(RuntimeError, match="migration failed"):
        with database.get_connection() as connection:
            connection.execute("BEGIN")
            connection.execute(
                "CREATE TABLE temporary_migration_table (id INTEGER)"
            )
            raise RuntimeError("migration failed")

    with database.get_connection() as connection:
        tables = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        version = connection.execute(
            "SELECT version FROM schema_version"
        ).fetchone()["version"]

    assert "temporary_migration_table" not in tables
    assert version == 1

def test_session_backfill_data_can_be_upserted_once(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        database,
        "DATABASE_PATH",
        tmp_path / "backfill.db",
    )
    database.initialize_database()

    profile = {
        "id": 232068332,
        "login": "codered2007",
        "name": None,
        "avatar_url": "https://example.com/avatar.png",
        "email": None,
    }

    database.upsert_user(profile)
    database.upsert_user(profile)

    with database.get_connection() as connection:
        rows = connection.execute(
            "SELECT github_id, login, name, email FROM users "
            "WHERE github_id = ?",
            (profile["id"],),
        ).fetchall()

    assert len(rows) == 1
    assert rows[0]["github_id"] == profile["id"]
    assert rows[0]["login"] == "codered2007"
    assert rows[0]["name"] is None
    assert rows[0]["email"] is None

def test_initialize_database_rolls_back_failed_schema_creation(
    tmp_path, monkeypatch
):
    db_path = tmp_path / "failed_initialization.db"
    monkeypatch.setattr(database, "DATABASE_PATH", db_path)

    # Create a database with a supported but incomplete schema.
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            "CREATE TABLE schema_version (version INTEGER NOT NULL)"
        )
        connection.execute(
            "INSERT INTO schema_version (version) VALUES (?)",
            (database.SCHEMA_VERSION,),
        )

    # Force a failure when initialization tries to create a table.
    original_connection = database.get_connection

    class FailingConnection:
        def __enter__(self):
            self.connection = original_connection()
            self.connection.execute("BEGIN")
            self.connection.execute(
                "CREATE TABLE temporary_test_table (id INTEGER)"
            )
            raise RuntimeError("migration failed")

        def __exit__(self, exc_type, exc_value, traceback):
            if self.connection:
                self.connection.rollback()
                self.connection.close()
            return False

    monkeypatch.setattr(
        database,
        "get_connection",
        lambda: FailingConnection(),
    )

    import pytest

    with pytest.raises(RuntimeError, match="migration failed"):
        database.initialize_database()

    # Inspect the file directly, without the patched connection.
    with sqlite3.connect(db_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }

    assert "temporary_test_table" not in tables
    assert "sessions" not in tables

def test_migration_registry_has_one_step_per_supported_version():
    assert database.SCHEMA_VERSION == 3
    assert hasattr(database, "MIGRATIONS")

    assert set(database.MIGRATIONS) == {1, 2, 3}

    assert all(
        callable(migration)
        for migration in database.MIGRATIONS.values()
    )

def test_registered_migration_failure_rolls_back_version(
    tmp_path, monkeypatch
):
    import pytest

    db_path = tmp_path / "migration_rollback.db"
    monkeypatch.setattr(database, "DATABASE_PATH", db_path)

    # Start at version 1 with the first migration already applied.
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            "CREATE TABLE schema_version (version INTEGER NOT NULL)"
        )
        connection.execute(
            "INSERT INTO schema_version (version) VALUES (1)"
        )
        connection.execute("""
            CREATE TABLE sessions (
                session_id TEXT PRIMARY KEY,
                session_data TEXT NOT NULL,
                expires_at REAL NOT NULL
            )
        """)
        connection.execute("""
            CREATE TABLE repository_indexes (
                user_id INTEGER NOT NULL,
                owner TEXT NOT NULL,
                repo TEXT NOT NULL,
                collection_name TEXT NOT NULL,
                updated_at REAL NOT NULL,
                PRIMARY KEY (user_id, owner, repo)
            )
        """)

    def failing_migration(connection):
        connection.execute(
            "CREATE TABLE migration_should_rollback (id INTEGER)"
        )
        raise RuntimeError("migration failed")

    monkeypatch.setitem(database.MIGRATIONS, 2, failing_migration)

    with pytest.raises(RuntimeError, match="migration failed"):
        database.initialize_database()

    with sqlite3.connect(db_path) as connection:
        version = connection.execute(
            "SELECT version FROM schema_version"
        ).fetchone()[0]
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }

    assert version == 1
    assert "migration_should_rollback" not in tables
    assert "workspaces" not in tables
