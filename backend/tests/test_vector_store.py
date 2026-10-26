
import sys
import types

import pytest
import chromadb

from app import database


# Keep unit tests independent of the installed ML dependency stack.
_embedding_stub = types.ModuleType("app.services.embedding_service")
_embedding_stub.generate_embedding = lambda text: [
    float(len(text) % 7),
    float(len(text) % 11),
    1.0,
]
sys.modules["app.services.embedding_service"] = _embedding_stub

from app.services import vector_store

@pytest.fixture
def isolated_vector_store(tmp_path, monkeypatch):
    monkeypatch.setattr(
        database,
        "DATABASE_PATH",
        tmp_path / "test_devpilot.db",
    )
    database.initialize_database()

    test_client = chromadb.PersistentClient(
        path=str(tmp_path / "chroma")
    )
    monkeypatch.setattr(vector_store, "client", test_client)

    # Keep all test vectors the same dimension without loading an
    # external embedding service for each test.
    monkeypatch.setattr(
        vector_store,
        "generate_embedding",
        lambda text: [
            float(len(text) % 7),
            float(len(text) % 11),
            1.0,
        ],
    )

    return vector_store


def chunk(path, content, start=1, end=1):
    return {
        "path": path,
        "content": content,
        "start_line": start,
        "end_line": end,
    }


def active_collection_name(store, user_id, owner, repo):
    return store._get_active_collection_name(
        user_id,
        owner,
        repo,
    )


def test_successful_reindex_removes_stale_chunks(
    isolated_vector_store,
):
    store = isolated_vector_store

    store.replace_code_chunks(
        1,
        "Owner",
        "Repo",
        [
            chunk("old.py", "old implementation"),
            chunk("shared.py", "first version"),
        ],
    )

    store.replace_code_chunks(
        1,
        "Owner",
        "Repo",
        [
            chunk("new.py", "new implementation"),
        ],
    )

    collection_name = active_collection_name(
        store,
        1,
        "Owner",
        "Repo",
    )
    collection = store.client.get_collection(
        name=collection_name,
    )
    result = collection.get(include=["documents", "metadatas"])

    assert result["ids"]
    assert {item["path"] for item in result["metadatas"]} == {
        "new.py"
    }
    assert result["documents"] == ["new implementation"]


def test_failed_preparation_preserves_active_index(
    isolated_vector_store,
    monkeypatch,
):
    store = isolated_vector_store

    store.replace_code_chunks(
        1,
        "Owner",
        "Repo",
        [chunk("stable.py", "known good implementation")],
    )

    old_name = active_collection_name(
        store,
        1,
        "Owner",
        "Repo",
    )

    def fail_preparation(_chunks):
        raise RuntimeError("Simulated embedding failure")

    monkeypatch.setattr(
        store,
        "_prepare_chunks",
        fail_preparation,
    )

    with pytest.raises(RuntimeError, match="embedding failure"):
        store.replace_code_chunks(
            1,
            "Owner",
            "Repo",
            [chunk("broken.py", "replacement")],
        )

    assert active_collection_name(
        store,
        1,
        "Owner",
        "Repo",
    ) == old_name

    collection = store.client.get_collection(name=old_name)
    result = collection.get(include=["documents", "metadatas"])

    assert result["documents"] == ["known good implementation"]
    assert result["metadatas"][0]["path"] == "stable.py"


def test_empty_repository_publishes_empty_index(
    isolated_vector_store,
):
    store = isolated_vector_store

    store.replace_code_chunks(
        1,
        "Owner",
        "Repo",
        [chunk("old.py", "old code")],
    )

    store.replace_code_chunks(
        1,
        "Owner",
        "Repo",
        [],
    )

    name = active_collection_name(store, 1, "Owner", "Repo")
    collection = store.client.get_collection(name=name)

    assert collection.count() == 0
    assert store.search_code(
        1,
        "Owner",
        "Repo",
        "old",
    ) == []


def test_repository_indexes_are_isolated_by_user(
    isolated_vector_store,
):
    store = isolated_vector_store

    store.replace_code_chunks(
        1,
        "Owner",
        "Repo",
        [chunk("one.py", "user one secret marker")],
    )
    store.replace_code_chunks(
        2,
        "Owner",
        "Repo",
        [chunk("two.py", "user two private marker")],
    )

    first_name = active_collection_name(
        store,
        1,
        "Owner",
        "Repo",
    )
    second_name = active_collection_name(
        store,
        2,
        "Owner",
        "Repo",
    )

    assert first_name != second_name

    first_collection = store.client.get_collection(name=first_name)
    second_collection = store.client.get_collection(name=second_name)

    assert first_collection.get()["metadatas"][0]["path"] == "one.py"
    assert second_collection.get()["metadatas"][0]["path"] == "two.py"


def test_identifier_detection_handles_python_identifiers(
    isolated_vector_store,
):
    store = isolated_vector_store

    assert store._is_exact_identifier_query("ask_ai")
    assert store._is_exact_identifier_query("_private")
    assert store._is_exact_identifier_query("get2")

    assert not store._is_exact_identifier_query("")
    assert not store._is_exact_identifier_query("two words")
    assert not store._is_exact_identifier_query("2get")

def test_failed_staging_write_preserves_active_index(
    isolated_vector_store,
    monkeypatch,
):
    store = isolated_vector_store

    store.replace_code_chunks(
        1,
        "Owner",
        "Repo",
        [chunk("stable.py", "known good implementation")],
    )

    old_name = active_collection_name(store, 1, "Owner", "Repo")
    original_create = store.client.create_collection

    class FailingCollection:
        def upsert(self, **kwargs):
            raise RuntimeError("Simulated staging write failure")

    def create_then_fail(*args, **kwargs):
        name = kwargs.get("name") or args[0]
        if name != old_name:
            return FailingCollection()
        return original_create(*args, **kwargs)

    monkeypatch.setattr(store.client, "create_collection", create_then_fail)

    with pytest.raises(RuntimeError, match="staging write failure"):
        store.replace_code_chunks(
            1,
            "Owner",
            "Repo",
            [chunk("replacement.py", "replacement implementation")],
        )

    assert active_collection_name(store, 1, "Owner", "Repo") == old_name
    old_collection = store.client.get_collection(name=old_name)
    assert old_collection.get(include=["documents"])["documents"] == [
        "known good implementation"
    ]


def test_failed_sqlite_publication_preserves_active_index(
    isolated_vector_store,
    monkeypatch,
):
    store = isolated_vector_store

    store.replace_code_chunks(
        1,
        "Owner",
        "Repo",
        [chunk("stable.py", "known good implementation")],
    )

    old_name = active_collection_name(store, 1, "Owner", "Repo")
    original_get_connection = store.get_connection

    class FailingConnection:
        def __enter__(self):
            raise RuntimeError("Simulated SQLite publication failure")

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(
        store,
        "get_connection",
        lambda: FailingConnection(),
    )

    with pytest.raises(RuntimeError, match="SQLite publication failure"):
        store.replace_code_chunks(
            1,
            "Owner",
            "Repo",
            [chunk("replacement.py", "replacement implementation")],
        )

    monkeypatch.setattr(store, "get_connection", original_get_connection)

    assert active_collection_name(store, 1, "Owner", "Repo") == old_name
    old_collection = store.client.get_collection(name=old_name)
    assert old_collection.get(include=["documents"])["documents"] == [
        "known good implementation"
    ]
