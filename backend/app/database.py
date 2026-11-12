
import json
import sqlite3
from pathlib import Path
import time
from uuid import uuid4
DATABASE_PATH = Path(__file__).resolve().parent.parent / "devpilot.db"
SCHEMA_VERSION = 8

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
def migrate_to_v4(connection):
    connection.execute("""
    CREATE TABLE IF NOT EXISTS repository_history (
        user_id INTEGER NOT NULL,
        owner TEXT NOT NULL COLLATE NOCASE,
        repo TEXT NOT NULL COLLATE NOCASE,
        name TEXT NOT NULL,
        description TEXT NOT NULL DEFAULT '',
        last_opened_at REAL NOT NULL,
        PRIMARY KEY (user_id, owner, repo),
        FOREIGN KEY (user_id)
            REFERENCES users(github_id)
            ON DELETE CASCADE
    )
""")

    connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_repository_history_user
        ON repository_history(user_id, last_opened_at DESC)
    """)

def migrate_to_v5(connection):
    connection.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            owner TEXT NOT NULL COLLATE NOCASE,
            repo TEXT NOT NULL COLLATE NOCASE,
            title TEXT NOT NULL DEFAULT 'New conversation',
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL,
            FOREIGN KEY (user_id)
                REFERENCES users(github_id)
                ON DELETE CASCADE
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS conversation_messages (
            id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
            content TEXT NOT NULL,
            sources TEXT NOT NULL DEFAULT '[]',
            created_at REAL NOT NULL,
            FOREIGN KEY (conversation_id)
                REFERENCES conversations(id)
                ON DELETE CASCADE
        )
    """)

    connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_conversations_user_repo
        ON conversations(user_id, owner, repo, updated_at DESC)
    """)

    connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_conversation_messages_conversation
        ON conversation_messages(conversation_id, created_at)
    """)

def migrate_to_v6(connection):
    connection.execute("""
        CREATE TABLE IF NOT EXISTS activities (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            owner TEXT NOT NULL COLLATE NOCASE,
            repo TEXT NOT NULL COLLATE NOCASE,
            action_type TEXT NOT NULL,
            title TEXT NOT NULL,
            status TEXT NOT NULL CHECK (
                status IN ('running', 'success', 'failed')
            ),
            details TEXT NOT NULL DEFAULT '{}',
            created_at REAL NOT NULL,
            completed_at REAL,
            FOREIGN KEY (user_id)
                REFERENCES users(github_id)
                ON DELETE CASCADE
        )
    """)

    connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_activities_user_repo
        ON activities(user_id, owner, repo, created_at DESC)
    """)

    connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_activities_user_created
        ON activities(user_id, created_at DESC)
    """)
def migrate_to_v7(connection):
    # User-saved repository summaries and analysis results.
    connection.execute("""
        CREATE TABLE IF NOT EXISTS saved_results (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            owner TEXT NOT NULL COLLATE NOCASE,
            repo TEXT NOT NULL COLLATE NOCASE,
            result_type TEXT NOT NULL CHECK (
                result_type IN (
                    'summary',
                    'review',
                    'architecture',
                    'dependency',
                    'security'
                )
            ),
            title TEXT NOT NULL,
            content TEXT NOT NULL DEFAULT '{}',
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL,
            FOREIGN KEY (user_id)
                REFERENCES users(github_id)
                ON DELETE CASCADE
        )
    """)

    connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_saved_results_user_repo
        ON saved_results(user_id, owner, repo, updated_at DESC)
    """)

    connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_saved_results_user_created
        ON saved_results(user_id, created_at DESC)
    """)

    # Persistent user preferences.
    connection.execute("""
        CREATE TABLE IF NOT EXISTS user_preferences (
            user_id INTEGER PRIMARY KEY,
            preferences TEXT NOT NULL DEFAULT '{}',
            updated_at REAL NOT NULL,
            FOREIGN KEY (user_id)
                REFERENCES users(github_id)
                ON DELETE CASCADE
        )
    """)

    # Persistent state belonging to a workspace.
    connection.execute("""
        CREATE TABLE IF NOT EXISTS workspace_state (
            id TEXT PRIMARY KEY,
            workspace_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            state_key TEXT NOT NULL,
            state_value TEXT NOT NULL DEFAULT '{}',
            updated_at REAL NOT NULL,
            UNIQUE (workspace_id, state_key),
            FOREIGN KEY (workspace_id)
                REFERENCES workspaces(id)
                ON DELETE CASCADE,
            FOREIGN KEY (user_id)
                REFERENCES users(github_id)
                ON DELETE CASCADE
        )
    """)

    connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_workspace_state_user
        ON workspace_state(user_id, workspace_id)
    """)

def migrate_to_v8(connection):
    """
    Scope repository history, conversations, activities, and saved
    results to workspaces while preserving all existing records.
    """

    # Ensure every existing user has at least one workspace.
    users = connection.execute(
        "SELECT github_id FROM users"
    ).fetchall()

    workspace_by_user = {}

    for user in users:
        user_id = user["github_id"]

        workspace = connection.execute(
            """
            SELECT id
            FROM workspaces
            WHERE user_id = ?
            ORDER BY created_at ASC, id ASC
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()

        if workspace is None:
            workspace_id = str(uuid4())
            now = time.time()

            connection.execute(
                """
                INSERT INTO workspaces (
                    id, user_id, name, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    workspace_id,
                    user_id,
                    "Personal Workspace",
                    now,
                    now,
                ),
            )
        else:
            workspace_id = workspace["id"]

        workspace_by_user[user_id] = workspace_id

    # Rebuild repository history with workspace ownership.
    connection.execute("""
        CREATE TABLE repository_history_v8 (
            user_id INTEGER NOT NULL,
            workspace_id TEXT NOT NULL,
            owner TEXT NOT NULL COLLATE NOCASE,
            repo TEXT NOT NULL COLLATE NOCASE,
            name TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            last_opened_at REAL NOT NULL,
            PRIMARY KEY (workspace_id, owner, repo),
            FOREIGN KEY (user_id)
                REFERENCES users(github_id) ON DELETE CASCADE,
            FOREIGN KEY (workspace_id)
                REFERENCES workspaces(id) ON DELETE CASCADE
        )
    """)

    history = connection.execute(
        "SELECT * FROM repository_history"
    ).fetchall()

    for row in history:
        connection.execute(
            """
            INSERT INTO repository_history_v8 (
                user_id, workspace_id, owner, repo,
                name, description, last_opened_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["user_id"],
                workspace_by_user[row["user_id"]],
                row["owner"],
                row["repo"],
                row["name"],
                row["description"],
                row["last_opened_at"],
            ),
        )

    connection.execute("DROP TABLE repository_history")
    connection.execute(
        "ALTER TABLE repository_history_v8 RENAME TO repository_history"
    )

    connection.execute("""
        CREATE INDEX idx_repository_history_workspace
        ON repository_history(user_id, workspace_id, last_opened_at DESC)
    """)

    # Rebuild conversations and their dependent messages.
    connection.execute("""
        CREATE TABLE conversations_v8 (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            workspace_id TEXT NOT NULL,
            owner TEXT NOT NULL COLLATE NOCASE,
            repo TEXT NOT NULL COLLATE NOCASE,
            title TEXT NOT NULL DEFAULT 'New conversation',
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL,
            FOREIGN KEY (user_id)
                REFERENCES users(github_id) ON DELETE CASCADE,
            FOREIGN KEY (workspace_id)
                REFERENCES workspaces(id) ON DELETE CASCADE
        )
    """)

    conversations = connection.execute(
        "SELECT * FROM conversations"
    ).fetchall()

    for row in conversations:
        connection.execute(
            """
            INSERT INTO conversations_v8 (
                id, user_id, workspace_id, owner, repo,
                title, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["id"],
                row["user_id"],
                workspace_by_user[row["user_id"]],
                row["owner"],
                row["repo"],
                row["title"],
                row["created_at"],
                row["updated_at"],
            ),
        )

    connection.execute("""
        CREATE TABLE conversation_messages_v8 (
            id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
            content TEXT NOT NULL,
            sources TEXT NOT NULL DEFAULT '[]',
            created_at REAL NOT NULL,
            FOREIGN KEY (conversation_id)
                REFERENCES conversations_v8(id) ON DELETE CASCADE
        )
    """)

    messages = connection.execute(
        "SELECT * FROM conversation_messages"
    ).fetchall()

    for row in messages:
        connection.execute(
            """
            INSERT INTO conversation_messages_v8 (
                id, conversation_id, role, content, sources, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                row["id"],
                row["conversation_id"],
                row["role"],
                row["content"],
                row["sources"],
                row["created_at"],
            ),
        )

    connection.execute("DROP TABLE conversation_messages")
    connection.execute("DROP TABLE conversations")

    connection.execute(
        "ALTER TABLE conversations_v8 RENAME TO conversations"
    )
    connection.execute(
        "ALTER TABLE conversation_messages_v8 "
        "RENAME TO conversation_messages"
    )

    connection.execute("""
        CREATE INDEX idx_conversations_workspace_repo
        ON conversations(user_id, workspace_id, owner, repo, updated_at DESC)
    """)

    connection.execute("""
        CREATE INDEX idx_conversation_messages_conversation
        ON conversation_messages(conversation_id, created_at)
    """)

    # Rebuild activities.
    connection.execute("""
        CREATE TABLE activities_v8 (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            workspace_id TEXT NOT NULL,
            owner TEXT NOT NULL COLLATE NOCASE,
            repo TEXT NOT NULL COLLATE NOCASE,
            action_type TEXT NOT NULL,
            title TEXT NOT NULL,
            status TEXT NOT NULL CHECK (
                status IN ('running', 'success', 'failed')
            ),
            details TEXT NOT NULL DEFAULT '{}',
            created_at REAL NOT NULL,
            completed_at REAL,
            FOREIGN KEY (user_id)
                REFERENCES users(github_id) ON DELETE CASCADE,
            FOREIGN KEY (workspace_id)
                REFERENCES workspaces(id) ON DELETE CASCADE
        )
    """)

    activities = connection.execute(
        "SELECT * FROM activities"
    ).fetchall()

    for row in activities:
        connection.execute(
            """
            INSERT INTO activities_v8 (
                id, user_id, workspace_id, owner, repo,
                action_type, title, status, details,
                created_at, completed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["id"],
                row["user_id"],
                workspace_by_user[row["user_id"]],
                row["owner"],
                row["repo"],
                row["action_type"],
                row["title"],
                row["status"],
                row["details"],
                row["created_at"],
                row["completed_at"],
            ),
        )

    connection.execute("DROP TABLE activities")
    connection.execute("ALTER TABLE activities_v8 RENAME TO activities")

    connection.execute("""
        CREATE INDEX idx_activities_workspace_repo
        ON activities(user_id, workspace_id, owner, repo, created_at DESC)
    """)

    connection.execute("""
        CREATE INDEX idx_activities_workspace_created
        ON activities(user_id, workspace_id, created_at DESC)
    """)

    # Rebuild saved results.
    connection.execute("""
        CREATE TABLE saved_results_v8 (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            workspace_id TEXT NOT NULL,
            owner TEXT NOT NULL COLLATE NOCASE,
            repo TEXT NOT NULL COLLATE NOCASE,
            result_type TEXT NOT NULL CHECK (
                result_type IN (
                    'summary',
                    'review',
                    'architecture',
                    'dependency',
                    'security'
                )
            ),
            title TEXT NOT NULL,
            content TEXT NOT NULL DEFAULT '{}',
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL,
            FOREIGN KEY (user_id)
                REFERENCES users(github_id) ON DELETE CASCADE,
            FOREIGN KEY (workspace_id)
                REFERENCES workspaces(id) ON DELETE CASCADE
        )
    """)

    results = connection.execute(
        "SELECT * FROM saved_results"
    ).fetchall()

    for row in results:
        connection.execute(
            """
            INSERT INTO saved_results_v8 (
                id, user_id, workspace_id, owner, repo,
                result_type, title, content, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["id"],
                row["user_id"],
                workspace_by_user[row["user_id"]],
                row["owner"],
                row["repo"],
                row["result_type"],
                row["title"],
                row["content"],
                row["created_at"],
                row["updated_at"],
            ),
        )

    connection.execute("DROP TABLE saved_results")
    connection.execute("ALTER TABLE saved_results_v8 RENAME TO saved_results")

    connection.execute("""
        CREATE INDEX idx_saved_results_workspace
        ON saved_results(user_id, workspace_id, updated_at DESC)
    """)

MIGRATIONS = {
    1: migrate_to_v1,
    2: migrate_to_v2,
    3: migrate_to_v3,
    4: migrate_to_v4,
    5: migrate_to_v5,
    6: migrate_to_v6,
    7: migrate_to_v7,
    8: migrate_to_v8,
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




def record_repository_open(
    user_id: int,
    workspace_id: str,
    owner: str,
    repo: str,
    name: str,
    description: str = "",
) -> None:
    """Record a repository opening within an owned workspace."""

    if not isinstance(user_id, int) or isinstance(user_id, bool):
        raise ValueError("Invalid user ID.")

    if not isinstance(workspace_id, str) or not workspace_id.strip():
        raise ValueError("Workspace ID is required.")

    if not all(
        isinstance(value, str) and value.strip()
        for value in (owner, repo, name)
    ):
        raise ValueError("Repository owner, name, and repository are required.")

    now = time.time()

    with get_connection() as connection:
        workspace = connection.execute(
            """
            SELECT id
            FROM workspaces
            WHERE id = ? AND user_id = ?
            """,
            (workspace_id, user_id),
        ).fetchone()

        if workspace is None:
            raise ValueError("Workspace not found.")

        connection.execute(
            """
            INSERT INTO repository_history (
                user_id, workspace_id, owner, repo,
                name, description, last_opened_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(workspace_id, owner, repo) DO UPDATE SET
                name = excluded.name,
                description = excluded.description,
                last_opened_at = excluded.last_opened_at
            """,
            (
                user_id,
                workspace_id,
                owner.strip(),
                repo.strip(),
                name.strip(),
                description.strip(),
                now,
            ),
        )


def get_repository_history(
    user_id: int,
    workspace_id: str,
    limit: int = 10,
) -> list[dict]:
    """Return recently opened repositories in an owned workspace."""

    if not isinstance(user_id, int) or isinstance(user_id, bool):
        raise ValueError("Invalid user ID.")

    if not isinstance(workspace_id, str) or not workspace_id.strip():
        raise ValueError("Workspace ID is required.")

    if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
        raise ValueError("History limit must be a positive integer.")

    with get_connection() as connection:
        workspace = connection.execute(
            """
            SELECT id
            FROM workspaces
            WHERE id = ? AND user_id = ?
            """,
            (workspace_id, user_id),
        ).fetchone()

        if workspace is None:
            raise ValueError("Workspace not found.")

        rows = connection.execute(
            """
            SELECT owner, repo, name, description, last_opened_at
            FROM repository_history
            WHERE user_id = ? AND workspace_id = ?
            ORDER BY last_opened_at DESC
            LIMIT ?
            """,
            (user_id, workspace_id, limit),
        ).fetchall()

    return [dict(row) for row in rows]


import uuid



def create_conversation(
    user_id: int,
    workspace_id: str,
    owner: str,
    repo: str,
    title: str = "New conversation",
) -> dict:
    """Create a conversation inside an owned workspace."""

    if not isinstance(user_id, int) or isinstance(user_id, bool):
        raise ValueError("Invalid user ID.")

    if not isinstance(workspace_id, str) or not workspace_id.strip():
        raise ValueError("Workspace ID is required.")

    if not all(
        isinstance(value, str) and value.strip()
        for value in (owner, repo, title)
    ):
        raise ValueError("Owner, repository, and title are required.")

    conversation_id = str(uuid.uuid4())
    now = time.time()

    with get_connection() as connection:
        workspace = connection.execute(
            """
            SELECT id
            FROM workspaces
            WHERE id = ? AND user_id = ?
            """,
            (workspace_id, user_id),
        ).fetchone()

        if workspace is None:
            raise ValueError("Workspace not found.")

        connection.execute(
            """
            INSERT INTO conversations (
                id, user_id, workspace_id, owner, repo,
                title, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                conversation_id,
                user_id,
                workspace_id,
                owner.strip(),
                repo.strip(),
                title.strip(),
                now,
                now,
            ),
        )

        row = connection.execute(
            """
            SELECT *
            FROM conversations
            WHERE id = ? AND user_id = ? AND workspace_id = ?
            """,
            (conversation_id, user_id, workspace_id),
        ).fetchone()

    return dict(row)


def list_conversations(
    user_id: int,
    workspace_id: str,
    owner: str,
    repo: str,
) -> list[dict]:
    """List conversations belonging to a workspace and repository."""

    with get_connection() as connection:
        workspace = connection.execute(
            """
            SELECT id
            FROM workspaces
            WHERE id = ? AND user_id = ?
            """,
            (workspace_id, user_id),
        ).fetchone()

        if workspace is None:
            raise ValueError("Workspace not found.")

        rows = connection.execute(
            """
            SELECT id, user_id, workspace_id, owner, repo,
                   title, created_at, updated_at
            FROM conversations
            WHERE user_id = ?
              AND workspace_id = ?
              AND owner = ?
              AND repo = ?
            ORDER BY updated_at DESC
            """,
            (user_id, workspace_id, owner, repo),
        ).fetchall()

    return [dict(row) for row in rows]


def add_conversation_message(
    conversation_id: str,
    role: str,
    content: str,
    sources: list[str] | None = None,
    user_id: int | None = None,
    workspace_id: str | None = None,
) -> dict:
    """Store a message only in a conversation owned by this workspace."""

    if role not in ("user", "assistant"):
        raise ValueError("Invalid message role.")

    if not isinstance(content, str) or not content.strip():
        raise ValueError("Message content is required.")

    if sources is None:
        sources = []

    if not isinstance(sources, list) or not all(
        isinstance(source, str) for source in sources
    ):
        raise ValueError("Invalid message sources.")

    if user_id is None or not isinstance(workspace_id, str) or not workspace_id.strip():
        raise ValueError("User and workspace are required.")

    message_id = str(uuid.uuid4())
    now = time.time()

    with get_connection() as connection:
        conversation = connection.execute(
            """
            SELECT id, title
            FROM conversations
            WHERE id = ? AND user_id = ? AND workspace_id = ?
            """,
            (conversation_id, user_id, workspace_id),
        ).fetchone()

        if conversation is None:
            raise ValueError("Conversation not found.")

        connection.execute(
            """
            INSERT INTO conversation_messages (
                id, conversation_id, role, content, sources, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                message_id,
                conversation_id,
                role,
                content,
                json.dumps(sources),
                now,
            ),
        )

        if role == "user" and conversation["title"] == "New conversation":
            title = " ".join(content.split())

            if len(title) > 60:
                title = title[:57] + "..."

            connection.execute(
                """
                UPDATE conversations
                SET title = ?, updated_at = ?
                WHERE id = ? AND user_id = ? AND workspace_id = ?
                """,
                (title, now, conversation_id, user_id, workspace_id),
            )
        else:
            connection.execute(
                """
                UPDATE conversations
                SET updated_at = ?
                WHERE id = ? AND user_id = ? AND workspace_id = ?
                """,
                (now, conversation_id, user_id, workspace_id),
            )

        row = connection.execute(
            """
            SELECT *
            FROM conversation_messages
            WHERE id = ?
            """,
            (message_id,),
        ).fetchone()

    result = dict(row)
    result["sources"] = json.loads(result["sources"])

    return result


def get_conversation_messages(
    conversation_id: str,
    user_id: int,
    workspace_id: str,
) -> list[dict] | None:
    """Retrieve messages only from the specified owned workspace."""

    with get_connection() as connection:
        conversation = connection.execute(
            """
            SELECT id
            FROM conversations
            WHERE id = ? AND user_id = ? AND workspace_id = ?
            """,
            (conversation_id, user_id, workspace_id),
        ).fetchone()

        if conversation is None:
            return None

        rows = connection.execute(
            """
            SELECT id, conversation_id, role, content, sources, created_at
            FROM conversation_messages
            WHERE conversation_id = ?
            ORDER BY created_at, id
            """,
            (conversation_id,),
        ).fetchall()

    messages = []

    for row in rows:
        message = dict(row)
        message["sources"] = json.loads(message["sources"])
        messages.append(message)

    return messages


def delete_conversation(
    conversation_id: str,
    user_id: int,
    workspace_id: str,
) -> bool:
    """Delete a conversation only within its owning workspace."""

    with get_connection() as connection:
        cursor = connection.execute(
            """
            DELETE FROM conversations
            WHERE id = ? AND user_id = ? AND workspace_id = ?
            """,
            (conversation_id, user_id, workspace_id),
        )

    return cursor.rowcount > 0


def get_conversation(
    conversation_id: str,
    user_id: int,
    workspace_id: str,
) -> dict | None:
    """Retrieve conversation metadata for its owner and workspace."""

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM conversations
            WHERE id = ? AND user_id = ? AND workspace_id = ?
            """,
            (conversation_id, user_id, workspace_id),
        ).fetchone()

    return dict(row) if row else None



def create_activity(
    user_id: int,
    workspace_id: str,
    owner: str,
    repo: str,
    action_type: str,
    title: str,
    details: dict | None = None,
) -> dict:
    """Create a running activity inside an owned workspace."""

    if not isinstance(user_id, int) or isinstance(user_id, bool):
        raise ValueError("Invalid user ID.")

    if not isinstance(workspace_id, str) or not workspace_id.strip():
        raise ValueError("Workspace ID is required.")

    if not all(
        isinstance(value, str) and value.strip()
        for value in (owner, repo, action_type, title)
    ):
        raise ValueError("Activity information is required.")

    if details is None:
        details = {}

    if not isinstance(details, dict):
        raise ValueError("Activity details must be a dictionary.")

    activity_id = str(uuid4())
    now = time.time()

    with get_connection() as connection:
        workspace = connection.execute(
            """
            SELECT id
            FROM workspaces
            WHERE id = ? AND user_id = ?
            """,
            (workspace_id, user_id),
        ).fetchone()

        if workspace is None:
            raise ValueError("Workspace not found.")

        connection.execute(
            """
            INSERT INTO activities (
                id, user_id, workspace_id, owner, repo,
                action_type, title, status, details,
                created_at, completed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 'running', ?, ?, NULL)
            """,
            (
                activity_id,
                user_id,
                workspace_id,
                owner.strip(),
                repo.strip(),
                action_type.strip(),
                title.strip(),
                json.dumps(details),
                now,
            ),
        )

        row = connection.execute(
            "SELECT * FROM activities WHERE id = ?",
            (activity_id,),
        ).fetchone()

    activity = dict(row)
    activity["details"] = json.loads(activity["details"])

    return activity


def complete_activity(
    activity_id: str,
    user_id: int,
    workspace_id: str,
    status: str,
    details: dict | None = None,
) -> dict | None:
    """Complete an activity only within its owning workspace."""

    if status not in ("success", "failed"):
        raise ValueError("Invalid activity completion status.")

    if details is not None and not isinstance(details, dict):
        raise ValueError("Activity details must be a dictionary.")

    if not isinstance(workspace_id, str) or not workspace_id.strip():
        raise ValueError("Workspace ID is required.")

    now = time.time()

    with get_connection() as connection:
        existing = connection.execute(
            """
            SELECT details
            FROM activities
            WHERE id = ?
              AND user_id = ?
              AND workspace_id = ?
              AND status = 'running'
            """,
            (activity_id, user_id, workspace_id),
        ).fetchone()

        if existing is None:
            return None

        activity_details = json.loads(existing["details"])

        if details:
            activity_details.update(details)

        connection.execute(
            """
            UPDATE activities
            SET status = ?, details = ?, completed_at = ?
            WHERE id = ?
              AND user_id = ?
              AND workspace_id = ?
              AND status = 'running'
            """,
            (
                status,
                json.dumps(activity_details),
                now,
                activity_id,
                user_id,
                workspace_id,
            ),
        )

        row = connection.execute(
            "SELECT * FROM activities WHERE id = ?",
            (activity_id,),
        ).fetchone()

    if row is None:
        return None

    activity = dict(row)
    activity["details"] = json.loads(activity["details"])

    return activity


def list_activities(
    user_id: int,
    workspace_id: str,
    owner: str | None = None,
    repo: str | None = None,
    limit: int = 50,
) -> list[dict]:
    """List activities belonging to one workspace."""

    if not isinstance(limit, int) or isinstance(limit, bool):
        raise ValueError("Invalid activity limit.")

    if limit < 1 or limit > 100:
        raise ValueError("Activity limit must be between 1 and 100.")

    if not isinstance(workspace_id, str) or not workspace_id.strip():
        raise ValueError("Workspace ID is required.")

    query = """
        SELECT *
        FROM activities
        WHERE user_id = ? AND workspace_id = ?
    """
    params = [user_id, workspace_id]

    if owner is not None:
        query += " AND owner = ?"
        params.append(owner)

    if repo is not None:
        query += " AND repo = ?"
        params.append(repo)

    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    with get_connection() as connection:
        workspace = connection.execute(
            """
            SELECT id
            FROM workspaces
            WHERE id = ? AND user_id = ?
            """,
            (workspace_id, user_id),
        ).fetchone()

        if workspace is None:
            raise ValueError("Workspace not found.")

        rows = connection.execute(query, params).fetchall()

    activities = []

    for row in rows:
        activity = dict(row)
        activity["details"] = json.loads(activity["details"])
        activities.append(activity)

    return activities


def get_activity(
    activity_id: str,
    user_id: int,
    workspace_id: str,
) -> dict | None:
    """Retrieve an activity belonging to its owner and workspace."""

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM activities
            WHERE id = ?
              AND user_id = ?
              AND workspace_id = ?
            """,
            (activity_id, user_id, workspace_id),
        ).fetchone()

    if row is None:
        return None

    activity = dict(row)
    activity["details"] = json.loads(activity["details"])

    return activity



def save_result(
    user_id: int,
    workspace_id: str,
    owner: str,
    repo: str,
    result_type: str,
    title: str,
    content: dict,
) -> dict:
    """Create a saved repository result in an owned workspace."""

    from uuid import uuid4

    allowed_types = {
        "summary",
        "review",
        "architecture",
        "dependency",
        "security",
    }

    if result_type not in allowed_types:
        raise ValueError("Invalid saved result type.")

    if not isinstance(content, dict):
        raise ValueError("Saved result content must be a dictionary.")

    if not workspace_id.strip():
        raise ValueError("Workspace ID is required.")

    if not owner.strip() or not repo.strip() or not title.strip():
        raise ValueError("Owner, repository, and title are required.")

    result_id = str(uuid4())
    now = time.time()

    with get_connection() as connection:
        workspace = connection.execute(
            """
            SELECT id
            FROM workspaces
            WHERE id = ? AND user_id = ?
            """,
            (workspace_id, user_id),
        ).fetchone()

        if workspace is None:
            raise ValueError("Workspace not found.")

        connection.execute(
            """
            INSERT INTO saved_results (
                id, user_id, workspace_id, owner, repo,
                result_type, title, content, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result_id,
                user_id,
                workspace_id,
                owner.strip(),
                repo.strip(),
                result_type,
                title.strip(),
                json.dumps(content),
                now,
                now,
            ),
        )

        row = connection.execute(
            """
            SELECT *
            FROM saved_results
            WHERE id = ? AND user_id = ? AND workspace_id = ?
            """,
            (result_id, user_id, workspace_id),
        ).fetchone()

    result = dict(row)
    result["content"] = json.loads(result["content"])
    return result


def list_saved_results(
    user_id: int,
    workspace_id: str,
    owner: str | None = None,
    repo: str | None = None,
    result_type: str | None = None,
    limit: int = 100,
) -> list[dict]:
    """List saved results belonging to one user and workspace."""

    if not isinstance(limit, int) or isinstance(limit, bool):
        raise ValueError("Invalid saved result limit.")

    if limit < 1 or limit > 100:
        raise ValueError("Saved result limit must be between 1 and 100.")

    with get_connection() as connection:
        workspace = connection.execute(
            """
            SELECT id
            FROM workspaces
            WHERE id = ? AND user_id = ?
            """,
            (workspace_id, user_id),
        ).fetchone()

        if workspace is None:
            raise ValueError("Workspace not found.")

        query = """
            SELECT *
            FROM saved_results
            WHERE user_id = ? AND workspace_id = ?
        """
        params = [user_id, workspace_id]

        if owner is not None:
            query += " AND owner = ?"
            params.append(owner)

        if repo is not None:
            query += " AND repo = ?"
            params.append(repo)

        if result_type is not None:
            query += " AND result_type = ?"
            params.append(result_type)

        query += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)

        rows = connection.execute(query, params).fetchall()

    results = []

    for row in rows:
        result = dict(row)
        result["content"] = json.loads(result["content"])
        results.append(result)

    return results


def get_saved_result(
    result_id: str,
    user_id: int,
    workspace_id: str,
) -> dict | None:
    """Retrieve one saved result from an owned workspace."""

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM saved_results
            WHERE id = ? AND user_id = ? AND workspace_id = ?
            """,
            (result_id, user_id, workspace_id),
        ).fetchone()

    if row is None:
        return None

    result = dict(row)
    result["content"] = json.loads(result["content"])
    return result


def delete_saved_result(
    result_id: str,
    user_id: int,
    workspace_id: str,
) -> bool:
    """Delete one saved result from an owned workspace."""

    with get_connection() as connection:
        cursor = connection.execute(
            """
            DELETE FROM saved_results
            WHERE id = ? AND user_id = ? AND workspace_id = ?
            """,
            (result_id, user_id, workspace_id),
        )

    return cursor.rowcount > 0



def get_user_preferences(user_id: int) -> dict:
    """Retrieve preferences belonging to one user."""

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT preferences
            FROM user_preferences
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()

    if row is None:
        return {}

    preferences = json.loads(row["preferences"])

    if not isinstance(preferences, dict):
        return {}

    return preferences


def update_user_preferences(
    user_id: int,
    preferences: dict,
) -> dict:
    """Create or update preferences belonging to one user."""

    if not isinstance(preferences, dict):
        raise ValueError("Preferences must be a dictionary.")

    try:
        serialized = json.dumps(preferences)
    except (TypeError, ValueError) as exc:
        raise ValueError("Preferences must contain valid JSON data.") from exc

    updated_at = time.time()

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO user_preferences (
                user_id,
                preferences,
                updated_at
            )
            VALUES (?, ?, ?)
            ON CONFLICT(user_id)
            DO UPDATE SET
                preferences = excluded.preferences,
                updated_at = excluded.updated_at
            """,
            (user_id, serialized, updated_at),
        )

    return preferences


def delete_user_preferences(user_id: int) -> bool:
    """Delete preferences belonging to one user."""

    with get_connection() as connection:
        cursor = connection.execute(
            """
            DELETE FROM user_preferences
            WHERE user_id = ?
            """,
            (user_id,),
        )

    return cursor.rowcount > 0

def get_workspace_state(
    workspace_id: str,
    user_id: int,
) -> dict | None:
    """Retrieve all state values for an owned workspace."""

    with get_connection() as connection:
        workspace = connection.execute(
            """
            SELECT id
            FROM workspaces
            WHERE id = ? AND user_id = ?
            """,
            (workspace_id, user_id),
        ).fetchone()

        if workspace is None:
            return None

        rows = connection.execute(
            """
            SELECT state_key, state_value
            FROM workspace_state
            WHERE workspace_id = ? AND user_id = ?
            """,
            (workspace_id, user_id),
        ).fetchall()

    return {
        row["state_key"]: json.loads(row["state_value"])
        for row in rows
    }


def set_workspace_state(
    workspace_id: str,
    user_id: int,
    state_key: str,
    state_value: dict,
) -> dict | None:
    """Create or update one state value in an owned workspace."""

    if not state_key.strip():
        raise ValueError("State key cannot be blank.")

    if not isinstance(state_value, dict):
        raise ValueError("State value must be a dictionary.")

    try:
        serialized = json.dumps(state_value)
    except (TypeError, ValueError) as exc:
        raise ValueError("State value must contain valid JSON data.") from exc

    updated_at = time.time()

    with get_connection() as connection:
        workspace = connection.execute(
            """
            SELECT id
            FROM workspaces
            WHERE id = ? AND user_id = ?
            """,
            (workspace_id, user_id),
        ).fetchone()

        if workspace is None:
            return None

        connection.execute(
            """
            INSERT INTO workspace_state (
                id,
                workspace_id,
                user_id,
                state_key,
                state_value,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(workspace_id, state_key)
            DO UPDATE SET
                state_value = excluded.state_value,
                updated_at = excluded.updated_at
            """,
            (
                str(uuid4()),
                workspace_id,
                user_id,
                state_key.strip(),
                serialized,
                updated_at,
            ),
        )

    return state_value


def delete_workspace_state(
    workspace_id: str,
    user_id: int,
    state_key: str,
) -> bool:
    """Delete one state value from an owned workspace."""

    with get_connection() as connection:
        cursor = connection.execute(
            """
            DELETE FROM workspace_state
            WHERE workspace_id = ?
              AND user_id = ?
              AND state_key = ?
            """,
            (workspace_id, user_id, state_key),
        )

    return cursor.rowcount > 0

