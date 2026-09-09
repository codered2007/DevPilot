import re

import chromadb

from app.services.embedding_service import (
    generate_embedding,
)


client = chromadb.PersistentClient(
    path="./data/chroma"
)


def get_collection(
    owner: str,
    repo: str,
):
    collection_name = (
        f"{owner}_{repo}"
        .replace("/", "_")
        .replace("-", "_")
    )

    return client.get_or_create_collection(
        name=collection_name
    )


def add_code_chunks(
    owner: str,
    repo: str,
    chunks: list[dict],
):
    collection = get_collection(
        owner,
        repo,
    )

    documents = []
    embeddings = []
    ids = []
    metadatas = []

    for index, chunk in enumerate(chunks):
        content = chunk.get(
            "content",
            "",
        )

        if not content.strip():
            continue

        embedding = generate_embedding(
            content
        )

        documents.append(content)
        embeddings.append(embedding)
        ids.append(
            f"{chunk['path']}:{chunk['start_line']}-{chunk['end_line']}:{index}"
        )
        metadatas.append(
            {
                "path": chunk["path"],
                "start_line": chunk["start_line"],
                "end_line": chunk["end_line"],
            }
        )

    if not documents:
        return

    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )


def _tokenize(
    text: str,
):
    return re.findall(
        r"[a-zA-Z0-9_]+",
        text.lower(),
    )


def _is_exact_identifier_query(
    query: str,
):
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

    # Exact match in source code.
    if query_lower in content_lower:
        score += 100

    # Exact match in file path.
    if query_lower in path_lower:
        score += 75

    # Strong boost when the query is actually defined
    # as a Python function in this chunk.
    definition_pattern = (
        rf"\b(?:async\s+)?def\s+"
        rf"{re.escape(query_lower)}\s*\("
    )

    if re.search(
        definition_pattern,
        content_lower,
    ):
        score += 1000

    query_tokens = set(
        _tokenize(query)
    )

    path_tokens = set(
        _tokenize(path)
    )

    content_tokens = set(
        _tokenize(content)
    )

    path_matches = len(
        query_tokens & path_tokens
    )

    content_matches = len(
        query_tokens & content_tokens
    )

    score += path_matches * 3
    score += content_matches

    return score


def search_code(
    owner: str,
    repo: str,
    query: str,
    limit: int = 8,
):
    collection = get_collection(
        owner,
        repo,
    )

    collection_count = collection.count()

    if collection_count == 0:
        return []

    query_embedding = generate_embedding(
        query
    )

    semantic_results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(
            30,
            collection_count,
        ),
    )

    semantic_documents = semantic_results.get(
        "documents",
        [[]],
    )[0]

    semantic_metadatas = semantic_results.get(
        "metadatas",
        [[]],
    )[0]

    semantic_distances = semantic_results.get(
        "distances",
        [[]],
    )[0]

    candidates = {}

    for index, document in enumerate(
        semantic_documents
    ):
        metadata = semantic_metadatas[index]

        key = (
            metadata["path"],
            metadata["start_line"],
            metadata["end_line"],
        )

        candidates[key] = {
            "path": metadata["path"],
            "content": document,
            "start_line": metadata[
                "start_line"
            ],
            "end_line": metadata[
                "end_line"
            ],
            "distance": semantic_distances[index],
        }

    all_results = collection.get(
        include=[
            "documents",
            "metadatas",
        ]
    )

    all_documents = all_results.get(
        "documents",
        [],
    )

    all_metadatas = all_results.get(
        "metadatas",
        [],
    )

    for index, document in enumerate(
        all_documents
    ):
        metadata = all_metadatas[index]

        key = (
            metadata["path"],
            metadata["start_line"],
            metadata["end_line"],
        )

        if key not in candidates:
            candidates[key] = {
                "path": metadata["path"],
                "content": document,
                "start_line": metadata[
                    "start_line"
                ],
                "end_line": metadata[
                    "end_line"
                ],
                "distance": 1.0,
            }

    exact_identifier_query = (
        _is_exact_identifier_query(query)
    )

    ranked = []

    for match in candidates.values():
        distance = match.get(
            "distance",
            1.0,
        )

        semantic_score = 1 / (
            1 + distance
        )

        keyword_score = _keyword_score(
            query,
            match["path"],
            match["content"],
        )

        exact_match = (
            query.strip().lower()
            in match["content"].lower()
        )

        definition_pattern = (
            rf"\b(?:async\s+)?def\s+"
            rf"{re.escape(query.strip().lower())}\s*\("
        )

        is_definition = bool(
            re.search(
                definition_pattern,
                match["content"].lower(),
            )
        )

        if (
            exact_identifier_query
            and is_definition
        ):
            final_score = (
                5000
                + keyword_score
                + semantic_score
            )

        elif (
            exact_identifier_query
            and exact_match
        ):
            final_score = (
                1000
                + keyword_score
                + semantic_score
            )

        else:
            final_score = (
                semantic_score
                + keyword_score * 0.01
            )

        match["keyword_score"] = (
            keyword_score
        )

        match["semantic_score"] = (
            semantic_score
        )

        match["score"] = final_score

        ranked.append(
            match
        )

    ranked.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return ranked[:limit]