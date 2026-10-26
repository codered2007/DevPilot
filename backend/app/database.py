
import json
import sqlite3
from pathlib import Path


DATABASE_PATH = Path(__file__).resolve().parent.parent / "devpilot.db"


def get_connection():
    connection = sqlite3.connect(
        DATABASE_PATH,
        timeout=10.0,
    )
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                session_data TEXT NOT NULL,
                expires_at REAL NOT NULL
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS repository_indexes (
                user_id INTEGER NOT NULL,
                owner TEXT NOT NULL,
                repo TEXT NOT NULL,
                collection_name TEXT NOT NULL,
                updated_at REAL NOT NULL,
                PRIMARY KEY (user_id, owner, repo)
            )
            """
        )


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
