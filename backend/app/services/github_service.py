import asyncio
import os
import re

import httpx
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

print("GitHub token loaded:", bool(GITHUB_TOKEN))

if GITHUB_TOKEN:
    print("Token prefix:", GITHUB_TOKEN[:4])
    print("Token length:", len(GITHUB_TOKEN))

HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "DevPilot",
}

if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"


STOP_WORDS = {
    "the",
    "is",
    "are",
    "was",
    "were",
    "where",
    "what",
    "when",
    "which",
    "who",
    "why",
    "how",
    "does",
    "did",
    "do",
    "this",
    "that",
    "these",
    "those",
    "for",
    "from",
    "with",
    "into",
    "about",
    "and",
    "or",
    "not",
    "can",
    "could",
    "would",
    "should",
    "will",
    "has",
    "have",
    "been",
    "its",
    "their",
    "they",
    "you",
    "your",
    "implemented",
    "implementation",
}


SOURCE_EXTENSIONS = {
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".py",
    ".java",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".cs",
    ".go",
    ".rs",
    ".rb",
    ".php",
    ".swift",
    ".kt",
    ".kts",
    ".scala",
    ".vue",
    ".svelte",
}


SOURCE_DIRECTORIES = {
    "src",
    "lib",
    "app",
    "core",
    "server",
    "services",
    "service",
    "adapters",
    "adapter",
    "api",
    "controllers",
    "controller",
    "components",
    "modules",
}


NON_SOURCE_DIRECTORIES = {
    "docs",
    "doc",
    ".github",
    "website",
    "examples",
    "example",
    "test",
    "tests",
    "__tests__",
}


def normalize_query(query: str):
    query = query.lower()

    words = re.findall(
        r"[a-zA-Z0-9_]+",
        query,
    )

    return [
        word
        for word in words
        if len(word) > 2
        and word not in STOP_WORDS
    ]


def get_path_score(
    path: str,
    query_words: list[str],
    query_text: str,
):
    normalized_path = path.lower()
    path_parts = normalized_path.split("/")

    score = 0

    # Exact query phrase matches in the path.
    if query_text and query_text in normalized_path:
        score += 15

    # Individual query terms in the path.
    for word in query_words:
        if word in normalized_path:
            score += 3

    # Source-code files are more useful for implementation questions.
    _, extension = os.path.splitext(normalized_path)

    if extension in SOURCE_EXTENSIONS:
        score += 4

    # Prioritize common implementation directories.
    for directory in path_parts[:-1]:
        if directory in SOURCE_DIRECTORIES:
            score += 5

        if directory in NON_SOURCE_DIRECTORIES:
            score -= 4

    # Files with implementation-oriented names get a bonus.
    filename = path_parts[-1]

    implementation_terms = {
        "adapter",
        "adapters",
        "service",
        "services",
        "controller",
        "controllers",
        "client",
        "request",
        "requests",
        "handler",
        "handlers",
        "core",
        "api",
    }

    for term in implementation_terms:
        if term in filename:
            score += 4

    return score


async def score_file_content(
    owner: str,
    repo: str,
    file: dict,
    query_words: list[str],
    query_text: str,
    filename_score: int,
):
    file_data = await get_file_content(
        owner,
        repo,
        file["path"],
    )

    score = filename_score

    if not file_data:
        return score, file

    raw_content = file_data.get(
        "content",
        "",
    )

    content = raw_content.lower()

    # Reward an exact phrase match.
    if query_text and query_text in content:
        score += 10

    # Score individual query terms based on frequency.
    for word in query_words:
        occurrences = content.count(word)

        # Cap the frequency contribution so a very common
        # word cannot dominate the ranking.
        score += min(occurrences, 10)

    return score, file


async def search_repository(
    owner: str,
    repo: str,
    query: str,
):
    tree = await get_repository_tree(
        owner,
        repo,
    )

    if tree is None:
        return []

    files = []

    for item in tree.get("tree", []):
        if item.get("type") != "blob":
            continue

        path = item.get("path", "")

        # Skip files that are unlikely to contain useful source code.
        if path.lower().endswith(
            (
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
            )
        ):
            continue

        files.append(
            {
                "path": path,
            }
        )

    query_words = normalize_query(query)

    if not query_words:
        query_words = [
            word.lower()
            for word in query.split()
            if len(word) > 2
        ]

    query_text = " ".join(query_words)

    scored_files = []

    for file in files:
        score = get_path_score(
            file["path"],
            query_words,
            query_text,
        )

        scored_files.append(
            (
                score,
                file,
            )
        )

    scored_files.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    # Take a candidate pool for content-based scoring.
    candidates = [
        file
        for score, file in scored_files[:20]
    ]

    # If there are too few candidates, add more files.
    if len(candidates) < 10:
        for file in files:
            if file not in candidates:
                candidates.append(file)

            if len(candidates) >= 20:
                break

    # Fetch candidate files concurrently.
    content_tasks = []

    for file in candidates:
        filename_score = next(
            (
                item_score
                for item_score, item_file
                in scored_files
                if item_file == file
            ),
            0,
        )

        content_tasks.append(
            score_file_content(
                owner,
                repo,
                file,
                query_words,
                query_text,
                filename_score,
            )
        )

    content_scored_files = await asyncio.gather(
        *content_tasks
    )

    content_scored_files.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    results = [
        file
        for score, file in content_scored_files
        if score > 0
    ]

    priority_files = [
        "README.md",
        "README",
        "package.json",
        "requirements.txt",
        "pyproject.toml",
        "setup.py",
        "Cargo.toml",
        "go.mod",
    ]

    for priority in priority_files:
        for file in files:
            if file["path"].lower() == priority.lower():
                if file not in results:
                    results.append(file)

                break

    print("Search query:", query)
    print("Normalized query:", query_words)
    print(
        "Search results:",
        [file["path"] for file in results[:8]],
    )

    return results[:8]


async def get_repository(
    owner: str,
    repo: str,
):
    url = f"https://api.github.com/repos/{owner}/{repo}"

    async with httpx.AsyncClient(
        follow_redirects=True
    ) as client:
        response = await client.get(
            url,
            headers=HEADERS,
        )

    print("=" * 50)
    print("GitHub URL:", url)
    print("Status:", response.status_code)
    print("=" * 50)

    if response.status_code != 200:
        print(response.text)
        return None

    return response.json()


async def get_repository_tree(
    owner: str,
    repo: str,
):
    url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repo}/git/trees/HEAD?recursive=1"
    )

    async with httpx.AsyncClient(
        follow_redirects=True
    ) as client:
        response = await client.get(
            url,
            headers=HEADERS,
        )

    print("=" * 50)
    print("Tree URL:", url)
    print("Status:", response.status_code)
    print("=" * 50)

    if response.status_code != 200:
        print(response.text)
        return None

    return response.json()


async def get_file_content(
    owner: str,
    repo: str,
    path: str,
):
    url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repo}/contents/{path}"
    )

    async with httpx.AsyncClient(
        follow_redirects=True
    ) as client:
        response = await client.get(
            url,
            headers=HEADERS,
        )

    if response.status_code != 200:
        print(response.text)
        return None

    return response.json()