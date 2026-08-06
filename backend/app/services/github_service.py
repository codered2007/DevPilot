import os

import httpx
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
print("GitHub token loaded:", bool(GITHUB_TOKEN))
print("Token prefix:", GITHUB_TOKEN[:4])
print("Token length:", len(GITHUB_TOKEN))
HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "DevPilot",
}

if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"


async def search_repository(owner: str, repo: str, query: str):
    tree = await get_repository_tree(owner, repo)

    if tree is None:
        return []

    results = []

    for item in tree["tree"]:
        if item["type"] != "blob":
            continue

        if query.lower() in item["path"].lower():
            results.append(
                {
                    "path": item["path"],
                }
            )

    return results


async def get_repository(owner: str, repo: str):
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


async def get_repository_tree(owner: str, repo: str):
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


async def get_file_content(owner: str, repo: str, path: str):
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