"""
Offline Chroma cleanup worker.

Run only when the FastAPI backend is stopped.
"""

import argparse
import logging

import chromadb

from app.database import (
    DATABASE_PATH,
    complete_chroma_cleanup,
    fail_chroma_cleanup,
    get_connection,
    get_pending_chroma_cleanup,
)
from app.services.vector_store import CHROMA_PATH


logger = logging.getLogger(__name__)


def collection_is_referenced(collection_name: str) -> bool:
    """Check whether an active repository index still uses this collection."""
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT 1
            FROM repository_indexes
            WHERE collection_name = ?
            LIMIT 1
            """,
            (collection_name,),
        ).fetchone()

    return row is not None


def process_cleanup_queue(limit: int = 20) -> dict:
    """Process queued collections without deleting active indexes."""
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH}"
        )

    if not CHROMA_PATH.exists():
        raise FileNotFoundError(
            f"Chroma storage not found: {CHROMA_PATH}"
        )

    client = chromadb.PersistentClient(path=str(CHROMA_PATH))

    results = {
        "processed": 0,
        "deleted": 0,
        "skipped": 0,
        "failed": 0,
    }

    tasks = get_pending_chroma_cleanup(limit)

    for task in tasks:
        collection_name = task["collection_name"]
        results["processed"] += 1

        try:
            if collection_is_referenced(collection_name):
                logger.warning(
                    "Skipping collection still referenced by an active index: %s",
                    collection_name,
                )
                results["skipped"] += 1
                continue

            try:
                client.delete_collection(name=collection_name)
            except chromadb.errors.NotFoundError:
                # The collection is already absent; cleanup is complete.
                pass

            # Verify absence before removing the queue entry.
            try:
                client.get_collection(name=collection_name)
            except chromadb.errors.NotFoundError:
                pass
            else:
                raise RuntimeError(
                    f"Collection still exists after deletion: {collection_name}"
                )

            if complete_chroma_cleanup(collection_name):
                results["deleted"] += 1
            else:
                raise RuntimeError(
                    "Collection was deleted, but its queue entry could not be removed."
                )

        except Exception as exc:
            fail_chroma_cleanup(
                collection_name,
                f"{type(exc).__name__}: {exc}",
            )
            results["failed"] += 1
            logger.exception(
                "Chroma cleanup failed for %s",
                collection_name,
            )

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Process pending DevPilot Chroma cleanup tasks."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of queued tasks to process.",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    results = process_cleanup_queue(args.limit)

    print("Chroma cleanup results:")
    for key, value in results.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()