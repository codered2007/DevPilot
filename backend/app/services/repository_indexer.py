
import base64
import binascii

from app.services.github_service import (
    get_repository_tree,
    get_file_content,
    chunk_code,
)

from app.services.vector_store import replace_code_chunks


SKIP_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".ico",
    ".lock",
    ".map",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
}

MAX_REPOSITORY_FILES = 2000
MAX_FILE_BYTES = 1_000_000
MAX_TOTAL_SOURCE_BYTES = 20_000_000


async def index_repository(
    owner: str,
    repo: str,
    token: str,
    user_id: int,
):
    tree = await get_repository_tree(
        owner,
        repo,
        token=token,
    )

    if tree is None:
        raise ValueError(
            "Unable to retrieve the repository tree."
        )

    tree_items = tree.get("tree")

    if not isinstance(tree_items, list):
        raise ValueError(
            "GitHub returned an invalid repository tree."
        )

    truncated = tree.get("truncated", False)

    if truncated:
        raise ValueError(
            "GitHub returned a truncated repository tree. "
            "The existing index was not replaced."
        )

    files = [
        item
        for item in tree_items
        if isinstance(item, dict)
        and item.get("type") == "blob"
        and isinstance(item.get("path"), str)
        and item["path"]
        and not item["path"].lower().endswith(
            tuple(SKIP_EXTENSIONS)
        )
    ]

    if len(files) > MAX_REPOSITORY_FILES:
        raise ValueError(
            f"Repository exceeds the indexing limit of "
            f"{MAX_REPOSITORY_FILES} files. "
            "The existing index was not replaced."
        )

    repository_chunks = []
    indexed_files = 0
    total_source_bytes = 0

    for item in files:
        path = item["path"]
        declared_size = item.get("size")

        if isinstance(declared_size, int) and declared_size > MAX_FILE_BYTES:
            continue

        file_data = await get_file_content(
            owner,
            repo,
            path,
            token=token,
        )

        # A missing or inaccessible file can indicate that the
        # repository changed during indexing. Abort rather than
        # publishing an incomplete index.
        if not isinstance(file_data, dict):
            raise ValueError(
                f"Unable to retrieve {path!r}. "
                "The existing index was not replaced."
            )

        encoded_content = file_data.get("content", "")

        if not isinstance(encoded_content, str):
            raise ValueError(
                f"Invalid content returned for {path!r}."
            )

        if not encoded_content.strip():
            continue

        try:
            normalized_content = "".join(encoded_content.split())

            raw_content = base64.b64decode(
                normalized_content,
     validate=True,
)
        except (binascii.Error, ValueError):
            raise ValueError(
                f"Invalid Base64 content returned for {path!r}. "
                "The existing index was not replaced."
            ) from None

        # GitHub may return an empty content field for files it
        # cannot provide through this endpoint. Do not index binary
        # data as source code.
        if len(raw_content) > MAX_FILE_BYTES:
            continue

        total_source_bytes += len(raw_content)

        if total_source_bytes > MAX_TOTAL_SOURCE_BYTES:
            raise ValueError(
                "Repository exceeds the total source-size limit. "
                "The existing index was not replaced."
            )

        try:
            content = raw_content.decode("utf-8")
        except UnicodeDecodeError:
            # Ignore binary or non-UTF-8 files.
            continue

        if not content.strip():
            continue

        chunks = chunk_code(content)
        file_chunks = []

        for chunk in chunks:
            file_chunks.append(
                {
                    "path": path,
                    "content": chunk["content"],
                    "start_line": chunk["start_line"],
                    "end_line": chunk["end_line"],
                }
            )

        if file_chunks:
            repository_chunks.extend(file_chunks)
            indexed_files += 1

    # This is the only point at which the active index is modified.
    # Embedding preparation errors propagate, preventing replacement
    # from starting when preparation fails.
    replace_code_chunks(
        user_id,
        owner,
        repo,
        repository_chunks,
    )

    return {
        "indexed_files": indexed_files,
        "indexed_chunks": len(repository_chunks),
    }
