import asyncio
import os
import re
import base64
import httpx
from dotenv import load_dotenv
from urllib.parse import quote


load_dotenv()

HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "DevPilot",
    "X-GitHub-Api-Version": "2022-11-28",
}


def _user_headers(token: str | None) -> dict[str, str]:
    """Build GitHub API headers using only the authenticated user token."""
    if not token:
        raise ValueError("A GitHub user token is required for repository operations.")
    return {**HEADERS, "Authorization": f"Bearer {token}"}


TIMEOUT = httpx.Timeout(
    30.0,
    connect=10.0,
)


def _is_github_rate_limited(response: httpx.Response) -> bool:
    """Detect primary and secondary GitHub API rate-limit responses."""
    if response.status_code == 429:
        return True

    if response.status_code != 403:
        return False

    if response.headers.get("Retry-After"):
        return True

    if response.headers.get("X-RateLimit-Remaining") == "0":
        return True

    try:
        message = response.json().get("message", "").lower()
    except (ValueError, AttributeError):
        return False

    return "rate limit" in message or "secondary rate" in message

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

    # Source-code files are more useful
    # for implementation questions.
    _, extension = os.path.splitext(normalized_path)

    if extension in SOURCE_EXTENSIONS:
        score += 4

    # Prioritize common implementation directories.
    for directory in path_parts[:-1]:
        if directory in SOURCE_DIRECTORIES:
            score += 5

        if directory in NON_SOURCE_DIRECTORIES:
            score -= 4

    # Files with implementation-oriented names
    # get a bonus.
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
    token: str | None = None,
):
    file_data = await get_file_content(
        owner,
        repo,
        file["path"],
        token=token,
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

        # Cap the frequency contribution so a
        # common word cannot dominate the ranking.
        score += min(occurrences, 10)

    return score, file



def chunk_code(
    content: str,
    chunk_size: int = 120,
    overlap: int = 20,
):
    lines = content.splitlines()

    if not lines:
        return []

    chunks = []

    start = 0

    while start < len(lines):
        end = min(
            start + chunk_size,
            len(lines),
        )

        chunk = "\n".join(
            lines[start:end]
        )

        if chunk.strip():
            chunks.append(
                {
                    "content": chunk,
                    "start_line": start + 1,
                    "end_line": end,
                }
            )

        if end >= len(lines):
            break

        start = end - overlap

    return chunks


async def search_repository_with_content(
    owner: str,
    repo: str,
    query: str,
    token: str | None = None,
):
    if not token:
        return []

    tree = await get_repository_tree(
        owner,
        repo,
        token=token,
    )

    if tree is None:
        return []

    files = []

    for item in tree.get("tree", []):
        if item.get("type") != "blob":
            continue

        path = item.get("path", "")

        # Skip files that are unlikely to contain
        # useful source code.
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

    # Take the best path-based candidates.
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

    async def retrieve_file(file):
        file_data = await get_file_content(
            owner,
            repo,
            file["path"],
            token=token,
        )

        if not file_data:
            return None

        raw_content = file_data.get(
            "content",
            "",
        )

        if not raw_content:
            return None

        return {
            "path": file["path"],
            "content": raw_content,
        }

    # Retrieve candidate contents concurrently.
    retrieved_files = await asyncio.gather(
        *[
            retrieve_file(file)
            for file in candidates
        ]
    )

    scored_results = []

    for file in retrieved_files:
        if not file:
            continue

        content = file["content"]

        chunks = chunk_code(content)

        for chunk in chunks:
            chunk_content = chunk["content"].lower()

            score = get_path_score(
                file["path"],
                query_words,
                query_text,
            )

            # Reward an exact phrase match.
            if (
                query_text
                and query_text in chunk_content
            ):
                score += 10

            # Score individual query terms based
            # on frequency inside the chunk.
            for word in query_words:
                occurrences = chunk_content.count(
                    word
                )

                # Cap the frequency contribution.
                score += min(occurrences, 10)

            scored_results.append(
                (
                    score,
                    {
                        "path": file["path"],
                        "content": chunk["content"],
                        "start_line": chunk["start_line"],
                        "end_line": chunk["end_line"],
                    },
                )
            )

    scored_results.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    results = [
        file
        for score, file in scored_results
        if score > 0
    ]

    return results[:8]



async def get_repository(
    owner: str,
    repo: str,
    token: str | None = None,
):
    if not token:
        return None

    url = f"https://api.github.com/repos/{owner}/{repo}"

    headers = _user_headers(token)

    try:
        async with httpx.AsyncClient(
            follow_redirects=False,
            timeout=TIMEOUT,
        ) as client:
            response = await client.get(
                url,
                headers=headers,
            )

        if response.status_code == 200:
            return response.json()

        if response.status_code == 404:
            return None

        response.raise_for_status()

    except httpx.HTTPStatusError:
        raise
    except httpx.RequestError:
        raise

    return None



async def get_repository_tree(
    owner: str,
    repo: str,
    token: str | None = None,
):
    if not token:
        return None

    url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repo}/git/trees/HEAD?recursive=1"
    )

    headers = _user_headers(token)

    try:
        async with httpx.AsyncClient(
            follow_redirects=False,
            timeout=TIMEOUT,
        ) as client:
            response = await client.get(
                url,
                headers=headers,
            )

            if response.status_code == 404:
                return None

            response.raise_for_status()
            return response.json()

    except httpx.HTTPStatusError:
        raise

    except httpx.RequestError:
        raise


async def get_file_content(
    owner: str,
    repo: str,
    path: str,
    token: str | None = None,
):
    if not token:
        return None

    encoded_path = quote(path.strip("/"), safe="/")
    url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repo}/contents/{encoded_path}"
    )

    headers = _user_headers(token)

    try:
        async with httpx.AsyncClient(
            follow_redirects=False,
            timeout=TIMEOUT,
        ) as client:
            response = await client.get(
                url,
                headers=headers,
            )

        if response.status_code == 404:
            return None

        response.raise_for_status()
        return response.json()

    except httpx.HTTPStatusError:
        raise

    except httpx.RequestError:
        raise


async def get_default_branch(
    owner: str,
    repo: str,
    token: str | None = None,
):
    if not token:
        return None

    url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repo}"
    )

    try:
        async with httpx.AsyncClient(
            follow_redirects=False,
            timeout=TIMEOUT,
        ) as client:
            response = await client.get(
                url,
                headers=_user_headers(token),
            )

            response.raise_for_status()

            data = response.json()

            return data.get(
                "default_branch"
            )

    except httpx.RequestError:
        raise


async def get_branch_sha(
    owner: str,
    repo: str,
    branch: str,
    token: str | None = None,
):
    if not token:
        return None

    url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repo}/git/ref/heads/"
        f"{branch}"
    )

    try:
        async with httpx.AsyncClient(
            follow_redirects=False,
            timeout=TIMEOUT,
        ) as client:
            response = await client.get(
                url,
                headers=_user_headers(token),
            )

            response.raise_for_status()

            data = response.json()

            return (
                data
                .get("object", {})
                .get("sha")
            )

    except httpx.RequestError:
        raise


async def create_branch(
    owner: str,
    repo: str,
    branch: str,
    base_sha: str,
    token: str | None = None,
):
    if not token:
        return None

    url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repo}/git/refs"
    )

    payload = {
        "ref": f"refs/heads/{branch}",
        "sha": base_sha,
    }

    try:
        async with httpx.AsyncClient(
            follow_redirects=False,
            timeout=TIMEOUT,
        ) as client:
            response = await client.post(
                url,
                headers=_user_headers(token),
                json=payload,
            )

            response.raise_for_status()

            data = response.json()

            return data.get(
                "ref"
            )

    except httpx.RequestError:
        raise


async def update_file_on_branch(
    owner: str,
    repo: str,
    path: str,
    content: str,
    branch: str,
    message: str,
    token: str | None = None,
):
    if not token:
        return None

    encoded_path = quote(path.strip("/"), safe="/")
    url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repo}/contents/{encoded_path}"
    )

    current_file = await get_file_content(
        owner,
        repo,
        path,
        token=token,
    )

    if not current_file:
        return None

    file_sha = current_file.get("sha")
    if not file_sha:
        return None

    encoded_content = base64.b64encode(
        content.encode("utf-8")
    ).decode("utf-8")

    payload = {
        "message": message,
        "content": encoded_content,
        "sha": file_sha,
        "branch": branch,
    }

    try:
        async with httpx.AsyncClient(
            follow_redirects=False,
            timeout=TIMEOUT,
        ) as client:
            response = await client.put(
                url,
                headers=_user_headers(token),
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            commit = data.get("commit", {})

            return {
                "path": path,
                "branch": branch,
                "commit_sha": commit.get("sha"),
                "commit_url": commit.get("html_url"),
            }

    except httpx.HTTPStatusError:
        raise
    except httpx.RequestError:
        raise


async def create_pull_request(
    owner: str,
    repo: str,
    title: str,
    body: str,
    head: str,
    base: str,
    token: str | None = None,
):
    if not token:
        return None

    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    payload = {
        "title": title,
        "body": body,
        "head": head,
        "base": base,
    }

    try:
        async with httpx.AsyncClient(
            follow_redirects=False,
            timeout=TIMEOUT,
        ) as client:
            response = await client.post(
                url,
                headers=_user_headers(token),
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            return {
                "number": data.get("number"),
                "title": data.get("title"),
                "url": data.get("html_url"),
                "state": data.get("state"),
                "head": data.get("head", {}).get("ref"),
                "base": data.get("base", {}).get("ref"),
            }

    except httpx.HTTPStatusError:
        raise
    except httpx.RequestError:
        raise


async def search_repository(
    owner: str,
    repo: str,
    query: str,
    token: str | None = None,
):
    """Search repository source files using the authenticated user token."""
    if not token:
        return []
    return await search_repository_with_content(
        owner, repo, query, token=token
    )
