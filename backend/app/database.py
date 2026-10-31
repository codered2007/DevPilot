
import json
import sqlite3
from pathlib import Path
import time

DATABASE_PATH = Path(__file__).resolve().parent.parent / "devpilot.db"
SCHEMA_VERSION = 3

def migrate_to_v1(connection):
    connection.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            session_data TEXT NOT NULL,
            expires_at REAL NOT NULL
        )
    """)
    connection.execute("""
        CREATE TABLE IF NOT EXISTS repository_indexes (
            user_id INTEGER NOT NULL,
            owner TEXT NOT NULL,
            repo TEXT NOT NULL,
            collection_name TEXT NOT NULL,
            updated_at REAL NOT NULL,
            PRIMARY KEY (user_id, owner, repo)
        )
    """)


def migrate_to_v2(connection):
    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            github_id INTEGER PRIMARY KEY,
            login TEXT NOT NULL,
            name TEXT,
            avatar_url TEXT,
            email TEXT,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        )
    """)
    connection.execute("""
        CREATE TABLE IF NOT EXISTS workspaces (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL,
            FOREIGN KEY (user_id)
                REFERENCES users(github_id)
                ON DELETE CASCADE
        )
    """)
    connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_workspaces_user_id
        ON workspaces(user_id)
    """)
def migrate_to_v3(connection):
    connection.execute("""
        CREATE TABLE IF NOT EXISTS chroma_cleanup_queue (
            collection_name TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at REAL NOT NULL,
            attempts INTEGER NOT NULL DEFAULT 0,
            last_error TEXT
        )
    """)

    connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_chroma_cleanup_user_id
        ON chroma_cleanup_queue(user_id)
    """)

MIGRATIONS = {
    1: migrate_to_v1,
    2: migrate_to_v2,
    3: migrate_to_v3,
}


def get_connection():
    connection = sqlite3.connect(
        DATABASE_PATH,
        timeout=10.0,
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection




def initialize_database():
    with get_connection() as connection:
        # Reject unsupported versions before modifying the database.
        tables = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }

        current_version = 0

        if "schema_version" in tables:
            versions = connection.execute(
                "SELECT version FROM schema_version"
            ).fetchall()

            if len(versions) > 1:
                raise RuntimeError(
                    "Database contains multiple schema versions."
                )

            if versions:
                current_version = versions[0]["version"]

                if current_version > SCHEMA_VERSION:
                    raise RuntimeError(
                        "Database schema version is newer than supported."
                    )

        connection.execute("BEGIN IMMEDIATE")

        connection.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER NOT NULL
            )
        """)

        # Databases without a version start at version zero.
        if current_version == 0:
            connection.execute(
                "DELETE FROM schema_version"
            )
            connection.execute(
                "INSERT INTO schema_version (version) VALUES (0)"
            )

        # Apply each migration and record its version in the same transaction.
        while current_version < SCHEMA_VERSION:
            next_version = current_version + 1
            migration = MIGRATIONS.get(next_version)

            if migration is None:
                raise RuntimeError(
                    f"Missing migration for schema version {next_version}."
                )

            migration(connection)

            connection.execute(
                "UPDATE schema_version SET version = ?",
                (next_version,),
            )
            current_version = next_version

        # Ensure the workspace index exists for previously created schemas.
        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_workspaces_user_id
            ON workspaces(user_id)
        """)

        # Backfill valid GitHub identities from existing sessions.
        session_rows = connection.execute(
            "SELECT session_data FROM sessions"
        ).fetchall()

        for row in session_rows:
            try:
                session = json.loads(row["session_data"])
                github_user = session.get("github_user", {})

                if not isinstance(github_user, dict):
                    continue

                github_id = github_user.get("id")
                login = github_user.get("login")

                if (
                    not isinstance(github_id, int)
                    or isinstance(github_id, bool)
                    or not isinstance(login, str)
                    or not login.strip()
                ):
                    continue

                now = time.time()

                connection.execute("""
                    INSERT INTO users (
                        github_id, login, name, avatar_url, email,
                        created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(github_id) DO UPDATE SET
                        login = excluded.login,
                        name = COALESCE(excluded.name, users.name),
                        avatar_url = COALESCE(
                            excluded.avatar_url, users.avatar_url
                        ),
                        email = COALESCE(excluded.email, users.email),
                        updated_at = excluded.updated_at
                """, (
                    github_id,
                    login.strip(),
                    github_user.get("name"),
                    github_user.get("avatar_url"),
                    github_user.get("email"),
                    now,
                    now,
                ))

            except (json.JSONDecodeError, AttributeError, TypeError):
                continue


def upsert_user(github_user: dict) -> None:
    import time

    github_id = github_user.get("id")
    login = github_user.get("login")

    if (
        not isinstance(github_id, int)
        or isinstance(github_id, bool)
        or not isinstance(login, str)
        or not login.strip()
    ):
        raise ValueError("Invalid GitHub user identity.")

    now = time.time()

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO users (
                github_id, login, name, avatar_url, email,
                created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(github_id) DO UPDATE SET
                login = excluded.login,
                name = excluded.name,
                avatar_url = excluded.avatar_url,
                email = excluded.email,
                updated_at = excluded.updated_at
            """,
            (
                github_id,
                login.strip(),
                github_user.get("name"),
                github_user.get("avatar_url"),
                github_user.get("email"),
                now,
                now,
            ),
        )


def create_workspace(
    workspace_id: str,
    user_id: int,
    name: str,
) -> None:
    import time

    if not workspace_id.strip() or not name.strip():
        raise ValueError("Workspace ID and name are required.")

    now = time.time()

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO workspaces (
                id, user_id, name, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (workspace_id, user_id, name.strip(), now, now),
        )


def list_workspaces(user_id: int) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, user_id, name, created_at, updated_at
            FROM workspaces
            WHERE user_id = ?
            ORDER BY created_at, id
            """,
            (user_id,),
        ).fetchall()

    return [dict(row) for row in rows]


def delete_workspace(workspace_id: str, user_id: int) -> bool:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            DELETE FROM workspaces
            WHERE id = ? AND user_id = ?
            """,
            (workspace_id, user_id),
        )

    return cursor.rowcount > 0


def save_session(session_id: str, session: dict) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT OR REPLACE INTO sessions
                (session_id, session_data, expires_at)
            VALUES (?, ?, ?)
            """,
            (
                session_id,
                json.dumps(session),
                session["expires_at"],
            ),
        )


def get_session(session_id: str) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT session_data
            FROM sessions
            WHERE session_id = ?
            """,
            (session_id,),
        ).fetchone()

    if row is None:
        return None

    return json.loads(row["session_data"])


def delete_session(session_id: str) -> None:
    with get_connection() as connection:
        connection.execute(
            "DELETE FROM sessions WHERE session_id = ?",
            (session_id,),
        )



def delete_user(user_id: int) -> bool:
    """Delete a user and queue their Chroma collections for cleanup."""
    if not isinstance(user_id, int) or isinstance(user_id, bool):
        raise ValueError("Invalid user ID.")

    with get_connection() as connection:
        user = connection.execute(
            "SELECT github_id FROM users WHERE github_id = ?",
            (user_id,),
        ).fetchone()

        if user is None:
            return False

        # Preserve collection names before deleting repository mappings.
        indexes = connection.execute(
            """
            SELECT collection_name
            FROM repository_indexes
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchall()

        now = time.time()

        for index in indexes:
            connection.execute(
                """
                INSERT OR IGNORE INTO chroma_cleanup_queue
                    (collection_name, user_id, created_at)
                VALUES (?, ?, ?)
                """,
                (index["collection_name"], user_id, now),
            )

        # Delete the user and associated workspaces.
        connection.execute(
            "DELETE FROM users WHERE github_id = ?",
            (user_id,),
        )

        # Remove all sessions belonging to this user.
        session_rows = connection.execute(
            "SELECT session_id, session_data FROM sessions"
        ).fetchall()

        for row in session_rows:
            try:
                session_data = json.loads(row["session_data"])
                github_user = session_data.get("github_user", {})

                if (
                    isinstance(github_user, dict)
                    and github_user.get("id") == user_id
                    and not isinstance(github_user.get("id"), bool)
                ):
                    connection.execute(
                        "DELETE FROM sessions WHERE session_id = ?",
                        (row["session_id"],),
                    )
            except (json.JSONDecodeError, AttributeError, TypeError):
                continue

        connection.execute(
            "DELETE FROM repository_indexes WHERE user_id = ?",
            (user_id,),
        )

    return True


def get_pending_chroma_cleanup(limit: int = 20) -> list[dict]:
    """Return pending Chroma cleanup tasks, oldest first."""
    if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
        raise ValueError("Cleanup limit must be a positive integer.")

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT collection_name, user_id, created_at, attempts, last_error
            FROM chroma_cleanup_queue
            ORDER BY created_at, collection_name
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [dict(row) for row in rows]


def complete_chroma_cleanup(collection_name: str) -> bool:
    """Remove a cleanup task after successful collection deletion."""
    with get_connection() as connection:
        cursor = connection.execute(
            """
            DELETE FROM chroma_cleanup_queue
            WHERE collection_name = ?
            """,
            (collection_name,),
        )

    return cursor.rowcount > 0


def fail_chroma_cleanup(collection_name: str, error: str) -> bool:
    """Record a failed cleanup attempt for a future retry."""
    if not isinstance(error, str) or not error.strip():
        raise ValueError("A cleanup error message is required.")

    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE chroma_cleanup_queue
            SET attempts = attempts + 1,
                last_error = ?
            WHERE collection_name = ?
            """,
            (error[:1000], collection_name),
        )

    return cursor.rowcount > 0