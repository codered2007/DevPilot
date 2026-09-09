from base64 import b64decode

from app.services.github_service import (
    get_repository_tree,
    get_file_content,
    chunk_code,
)

from app.services.vector_store import (
    add_code_chunks,
)


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


async def index_repository(
    owner: str,
    repo: str,
):
    tree = await get_repository_tree(
        owner,
        repo,
    )

    if tree is None:
        return {
            "indexed_files": 0,
            "indexed_chunks": 0,
        }

    indexed_files = 0
    indexed_chunks = 0

    for item in tree.get("tree", []):
        if item.get("type") != "blob":
            continue

        path = item.get(
            "path",
            "",
        )

        if path.lower().endswith(
            tuple(SKIP_EXTENSIONS)
        ):
            continue

        file_data = await get_file_content(
            owner,
            repo,
            path,
        )

        if not file_data:
            continue

        encoded_content = file_data.get(
            "content",
            "",
        )

        if not encoded_content.strip():
            continue

        try:
            content = b64decode(
                encoded_content
            ).decode(
                "utf-8",
                errors="ignore",
            )
        except Exception:
            continue

        if not content.strip():
            continue

        chunks = chunk_code(
            content
        )

        repository_chunks = []

        for chunk in chunks:
            repository_chunks.append(
                {
                    "path": path,
                    "content": chunk["content"],
                    "start_line": chunk[
                        "start_line"
                    ],
                    "end_line": chunk[
                        "end_line"
                    ],
                }
            )

        if not repository_chunks:
            continue

        add_code_chunks(
            owner,
            repo,
            repository_chunks,
        )

        indexed_files += 1
        indexed_chunks += len(
            repository_chunks
        )

    return {
        "indexed_files": indexed_files,
        "indexed_chunks": indexed_chunks,
    }