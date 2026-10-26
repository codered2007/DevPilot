import threading
from contextlib import contextmanager
import hashlib
import json
import re
import time
import uuid
from pathlib import Path
import chromadb

from app.database import get_connection
from app.services.embedding_service import generate_embedding


# Preserve the existing relative path to avoid silently switching databases.
CHROMA_PATH = Path(__file__).resolve().parents[2] / "data" / "chroma"
client = chromadb.PersistentClient(path=str(CHROMA_PATH))
MAX_SEARCH_LIMIT = 30
_LOCKS_GUARD = threading.Lock()
_REPOSITORY_LOCKS = {}


@contextmanager
def _repository_lock(identity):
    with _LOCKS_GUARD:
        lock = _REPOSITORY_LOCKS.setdefault(
            identity,
            threading.RLock(),
        )

    with lock:
        yield

def _repository_identity(user_id: int, owner: str, repo: str):
    return (
        user_id,
        owner.strip().lower(),
        repo.strip().lower(),
    )


def _legacy_collection_name(user_id: int, owner: str, repo: str) -> str:
    identity = json.dumps(
        list(_repository_identity(user_id, owner, repo)),
        separators=(",", ":"),
    )
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()
    return f"repo_{digest}"


def _get_active_collection_name(
    user_id: int,
    owner: str,
    repo: str,
) -> str | None:
    identity = _repository_identity(user_id, owner, repo)

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT collection_name
            FROM repository_indexes
            WHERE user_id = ? AND owner = ? AND repo = ?
            """,
            identity,
        ).fetchone()

    return row["collection_name"] if row else None


def get_collection(
    user_id: int,
    owner: str,
    repo: str,
):
    """Resolve the active collection, falling back to the legacy index."""
    active_name = _get_active_collection_name(user_id, owner, repo)

    if active_name:
        return client.get_collection(name=active_name)

    # Preserve compatibility with indexes created before versioned indexing.
    return client.get_or_create_collection(
        name=_legacy_collection_name(user_id, owner, repo)
    )


def _prepare_chunks(chunks: list[dict]):
    documents = []
    embeddings = []
    ids = []
    metadatas = []

    for chunk in chunks:
        content = chunk.get("content", "")

        if not isinstance(content, str) or not content.strip():
            continue

        path = chunk.get("path")
        start_line = chunk.get("start_line")
        end_line = chunk.get("end_line")

        if (
            not isinstance(path, str)
            or not path
            or not isinstance(start_line, int)
            or isinstance(start_line, bool)
            or not isinstance(end_line, int)
            or isinstance(end_line, bool)
            or start_line < 1
            or end_line < start_line
        ):
            raise ValueError("Invalid code chunk metadata.")

        chunk_identity = json.dumps(
            [path, start_line, end_line],
            separators=(",", ":"),
        )
        chunk_id = hashlib.sha256(
            chunk_identity.encode("utf-8")
        ).hexdigest()

        embedding = generate_embedding(content)

        documents.append(content)
        embeddings.append(embedding)
        ids.append(chunk_id)
        metadatas.append(
            {
                "path": path,
                "start_line": start_line,
                "end_line": end_line,
            }
        )

    return documents, embeddings, ids, metadatas


def add_code_chunks(
    user_id: int,
    owner: str,
    repo: str,
    chunks: list[dict],
):
    """Add or update chunks in the currently selected collection."""
    documents, embeddings, ids, metadatas = _prepare_chunks(chunks)

    if not documents:
        return

    collection = get_collection(user_id, owner, repo)
    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )



def replace_code_chunks(
    user_id: int,
    owner: str,
    repo: str,
    chunks: list[dict],
):
    """
    Build and publish a complete new index while serializing replacements
    for the same repository within this Python process.
    """
    identity = _repository_identity(user_id, owner, repo)

    with _repository_lock(identity):
        documents, embeddings, ids, metadatas = _prepare_chunks(chunks)

        legacy_name = _legacy_collection_name(user_id, owner, repo)
        old_name = _get_active_collection_name(user_id, owner, repo)

        staging_name = (
            f"repo_{hashlib.sha256(repr(identity).encode()).hexdigest()}_"
            f"{uuid.uuid4().hex}"
        )

        staging_created = False

        try:
            staging = client.create_collection(name=staging_name)
            staging_created = True

            if ids:
                staging.upsert(
                    ids=ids,
                    documents=documents,
                    embeddings=embeddings,
                    metadatas=metadatas,
                )

            # Publish only after the complete staging collection is ready.
            with get_connection() as connection:
                connection.execute(
                    """
                    INSERT INTO repository_indexes
                        (user_id, owner, repo, collection_name, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(user_id, owner, repo)
                    DO UPDATE SET
                        collection_name = excluded.collection_name,
                        updated_at = excluded.updated_at
                    """,
                    (*identity, staging_name, time.time()),
                )

        except Exception:
            if staging_created:
                try:
                    client.delete_collection(name=staging_name)
                except Exception:
                    # Preserve the original error if cleanup also fails.
                    pass
            raise


def _tokenize(text: str):
    return re.findall(r"[a-zA-Z0-9_]+", text.lower())


def _is_exact_identifier_query(query: str):
    return bool(
        re.fullmatch(
            r"[a-zA-Z_][a-zA-Z0-9_]*",
            query.strip(),
        )
    )


def _keyword_score(
    query: str,
    path: str,
    content: str,
):
    query_lower = query.strip().lower()
    path_lower = path.lower()
    content_lower = content.lower()

    score = 0

    if query_lower and query_lower in content_lower:
        score += 100

    if query_lower and query_lower in path_lower:
        score += 75

    definition_pattern = (
        rf"\b(?:async\s+)?def\s+"
        rf"{re.escape(query_lower)}\s*\("
    )

    if _is_exact_identifier_query(query) and re.search(
        definition_pattern,
        content_lower,
    ):
        score += 1000

    query_tokens = set(_tokenize(query))
    path_tokens = set(_tokenize(path))
    content_tokens = set(_tokenize(content))

    score += len(query_tokens & path_tokens) * 3
    score += len(query_tokens & content_tokens)

    return score


def search_code(
    user_id: int,
    owner: str,
    repo: str,
    query: str,
    limit: int = 8,
):
    if not isinstance(query, str) or not query.strip():
        return []

    if not isinstance(limit, int) or isinstance(limit, bool):
        raise ValueError("Search limit must be an integer.")

    if limit < 1:
        raise ValueError("Search limit must be at least 1.")

    limit = min(limit, MAX_SEARCH_LIMIT)
    collection = get_collection(user_id, owner, repo)
    collection_count = collection.count()

    if collection_count == 0:
        return []

    query_embedding = generate_embedding(query)
    result_count = min(30, collection_count)

    semantic_results = collection.query(
        query_embeddings=[query_embedding],
        n_results=result_count,
        include=["documents", "metadatas", "distances"],
    )

    documents = (semantic_results.get("documents") or [[]])[0]
    metadatas = (semantic_results.get("metadatas") or [[]])[0]
    distances = (semantic_results.get("distances") or [[]])[0]

    candidates = {}

    for index, document in enumerate(documents):
        if not isinstance(document, str) or index >= len(metadatas):
            continue

        metadata = metadatas[index]

        if not isinstance(metadata, dict):
            continue

        path = metadata.get("path")
        start_line = metadata.get("start_line")
        end_line = metadata.get("end_line")

        if (
            not isinstance(path, str)
            or not isinstance(start_line, int)
            or isinstance(start_line, bool)
            or not isinstance(end_line, int)
            or isinstance(end_line, bool)
            or start_line < 1
            or end_line < start_line
        ):
            continue

        distance = distances[index] if index < len(distances) else 1.0
        key = (path, start_line, end_line)

        candidates[key] = {
            "path": path,
            "content": document,
            "start_line": start_line,
            "end_line": end_line,
            "distance": distance,
        }

    exact_identifier_query = _is_exact_identifier_query(query)
    ranked = []

    for match in candidates.values():
        distance = match["distance"]
        semantic_score = 1 / (1 + max(0.0, distance))

        keyword_score = _keyword_score(
            query,
            match["path"],
            match["content"],
        )

        content_lower = match["content"].lower()
        query_lower = query.strip().lower()
        exact_match = query_lower in content_lower

        definition_pattern = (
            rf"\b(?:async\s+)?def\s+"
            rf"{re.escape(query_lower)}\s*\("
        )

        is_definition = (
            exact_identifier_query
            and bool(re.search(definition_pattern, content_lower))
        )

        if is_definition:
            final_score = 5000 + keyword_score + semantic_score
        elif exact_identifier_query and exact_match:
            final_score = 1000 + keyword_score + semantic_score
        else:
            final_score = semantic_score + keyword_score * 0.01

        match["keyword_score"] = keyword_score
        match["semantic_score"] = semantic_score
        match["score"] = final_score
        ranked.append(match)

    ranked.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return ranked[:limit]
