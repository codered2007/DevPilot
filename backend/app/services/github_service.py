import os

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


async def search_repository(
    owner: str,
    repo: str,
    query: str,
):
    tree = await get_repository_tree(owner, repo)

    if tree is None:
        return []

    files = []

    for item in tree.get("tree", []):
        if item.get("type") != "blob":
            continue

        path = item.get("path", "")

        files.append(
            {
                "path": path,
            }
        )

    query_words = {
        word.lower()
        for word in query.split()
        if len(word) > 2
    }

    scored_files = []

    for file in files:
        path = file["path"].lower()

        score = 0

        for word in query_words:
            if word in path:
                score += 1

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

    results = [
        file
        for score, file in scored_files
        if score > 0
    ]

    if not results:
        priority_files = [
            "README.md",
            "README",
            "package.json",
            "pyproject.toml",
            "requirements.txt",
            "setup.py",
            "Cargo.toml",
            "go.mod",
        ]

        for priority in priority_files:
            for file in files:
                if file["path"].lower() == priority.lower():
                    results.append(file)

                    if len(results) >= 5:
                        return results

    return results[:5]


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