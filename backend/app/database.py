
import json
import sqlite3
from pathlib import Path
import time

DATABASE_PATH = Path(__file__).resolve().parent.parent / "devpilot.db"
SCHEMA_VERSION = 5

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

MIGRATIONS = {
    1: migrate_to_v1,
    2: migrate_to_v2,
    3: migrate_to_v3,
    4: migrate_to_v4,
    5: migrate_to_v5,
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
    owner: str,
    repo: str,
    name: str,
    description: str = "",
) -> None:
    """Record a repository opening or update its last-opened timestamp."""

    if not isinstance(user_id, int) or isinstance(user_id, bool):
        raise ValueError("Invalid user ID.")

    if not all(
        isinstance(value, str) and value.strip()
        for value in (owner, repo, name)
    ):
        raise ValueError("Repository owner, name, and display name are required.")

    if not isinstance(description, str):
        raise ValueError("Invalid repository description.")

    now = time.time()

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO repository_history (
                user_id, owner, repo, name, description, last_opened_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, owner, repo) DO UPDATE SET
                name = excluded.name,
                description = excluded.description,
                last_opened_at = excluded.last_opened_at
            """,
            (
                user_id,
                owner.strip(),
                repo.strip(),
                name.strip(),
                description.strip(),
                now,
            ),
        )


def get_repository_history(
    user_id: int,
    limit: int = 10,
) -> list[dict]:
    """Return a user's recently opened repositories."""

    if not isinstance(user_id, int) or isinstance(user_id, bool):
        raise ValueError("Invalid user ID.")

    if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
        raise ValueError("History limit must be a positive integer.")

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT owner, repo, name, description, last_opened_at
            FROM repository_history
            WHERE user_id = ?
            ORDER BY last_opened_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()

    return [dict(row) for row in rows]


import uuid


def create_conversation(
    user_id: int,
    owner: str,
    repo: str,
    title: str = "New conversation",
) -> dict:
    """Create a conversation belonging to a user and repository."""

    if not isinstance(user_id, int) or isinstance(user_id, bool):
        raise ValueError("Invalid user ID.")

    if not all(
        isinstance(value, str) and value.strip()
        for value in (owner, repo, title)
    ):
        raise ValueError("Owner, repository, and title are required.")

    conversation_id = str(uuid.uuid4())
    now = time.time()

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO conversations (
                id, user_id, owner, repo, title, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                conversation_id,
                user_id,
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
            WHERE id = ? AND user_id = ?
            """,
            (conversation_id, user_id),
        ).fetchone()

    return dict(row)


def list_conversations(
    user_id: int,
    owner: str,
    repo: str,
) -> list[dict]:
    """List conversations for one user and repository."""

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, user_id, owner, repo, title, created_at, updated_at
            FROM conversations
            WHERE user_id = ? AND owner = ? AND repo = ?
            ORDER BY updated_at DESC
            """,
            (user_id, owner, repo),
        ).fetchall()

    return [dict(row) for row in rows]



def add_conversation_message(
    conversation_id: str,
    role: str,
    content: str,
    sources: list[str] | None = None,
) -> dict:
    """Store a message and update conversation metadata."""

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

    message_id = str(uuid.uuid4())
    now = time.time()

    with get_connection() as connection:
        conversation = connection.execute(
            """
            SELECT id, title
            FROM conversations
            WHERE id = ?
            """,
            (conversation_id,),
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

        if (
            role == "user"
            and conversation["title"] == "New conversation"
        ):
            title = " ".join(content.split())

            if len(title) > 60:
                title = title[:57] + "..."

            connection.execute(
                """
                UPDATE conversations
                SET title = ?, updated_at = ?
                WHERE id = ?
                """,
                (title, now, conversation_id),
            )
        else:
            connection.execute(
                """
                UPDATE conversations
                SET updated_at = ?
                WHERE id = ?
                """,
                (now, conversation_id),
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
) -> list[dict] | None:
    """Retrieve messages only if the conversation belongs to the user."""

    with get_connection() as connection:
        conversation = connection.execute(
            """
            SELECT id
            FROM conversations
            WHERE id = ? AND user_id = ?
            """,
            (conversation_id, user_id),
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
) -> bool:
    """Delete a user's conversation and cascade-delete its messages."""

    with get_connection() as connection:
        cursor = connection.execute(
            """
            DELETE FROM conversations
            WHERE id = ? AND user_id = ?
            """,
            (conversation_id, user_id),
        )

    return cursor.rowcount > 0

def get_conversation(
    conversation_id: str,
    user_id: int,
) -> dict | None:
    """Retrieve conversation metadata for its owner only."""

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM conversations
            WHERE id = ? AND user_id = ?
            """,
            (conversation_id, user_id),
        ).fetchone()

    return dict(row) if row else None
