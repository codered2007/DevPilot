import chromadb
import pytest

from app import database
from app.services import chroma_cleanup_worker as worker


@pytest.fixture
def isolated_cleanup_worker(tmp_path, monkeypatch):
    db_path = tmp_path / "cleanup_test.db"
    chroma_path = tmp_path / "chroma"

    monkeypatch.setattr(database, "DATABASE_PATH", db_path)
    monkeypatch.setattr(worker, "CHROMA_PATH", chroma_path)

    database.initialize_database()

    client = chromadb.PersistentClient(path=str(chroma_path))

    return client


def add_cleanup_task(collection_name, user_id=1):
    with database.get_connection() as connection:
        connection.execute(
            """
            INSERT INTO chroma_cleanup_queue
                (collection_name, user_id, created_at)
            VALUES (?, ?, ?)
            """,
            (collection_name, user_id, 1000.0),
        )


def test_worker_deletes_queued_collection(isolated_cleanup_worker):
    client = isolated_cleanup_worker
    collection = client.create_collection("cleanup_test_collection")
    collection.add(
        ids=["doc-1"],
        documents=["test document"],
    )

    add_cleanup_task("cleanup_test_collection")

    results = worker.process_cleanup_queue()

    assert results["deleted"] == 1
    assert results["failed"] == 0

    with pytest.raises(Exception):
        client.get_collection("cleanup_test_collection")

    assert database.get_pending_chroma_cleanup() == []


def test_worker_skips_active_collection(isolated_cleanup_worker):
    client = isolated_cleanup_worker
    collection_name = "active_collection"

    client.create_collection(collection_name)

    with database.get_connection() as connection:
        connection.execute(
            """
            INSERT INTO repository_indexes
                (user_id, owner, repo, collection_name, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (1, "owner", "repo", collection_name, 1000.0),
        )

    add_cleanup_task(collection_name)

    results = worker.process_cleanup_queue()

    assert results["skipped"] == 1
    assert client.get_collection(collection_name) is not None
    assert len(database.get_pending_chroma_cleanup()) == 1


def test_worker_records_failed_deletion(
    isolated_cleanup_worker,
    monkeypatch,
):
    add_cleanup_task("failed_collection")

    class FailingClient:
        def delete_collection(self, name):
            raise RuntimeError("Simulated deletion failure")

        def get_collection(self, name):
            raise RuntimeError("Collection lookup failed")

    monkeypatch.setattr(
        worker.chromadb,
        "PersistentClient",
        lambda path: FailingClient(),
    )

    results = worker.process_cleanup_queue()

    assert results["failed"] == 1

    task = database.get_pending_chroma_cleanup()[0]
    assert task["attempts"] == 1
    assert "Simulated deletion failure" in task["last_error"]