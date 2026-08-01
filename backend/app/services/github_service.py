import httpx


async def get_repository(owner: str, repo: str):
    url = f"https://api.github.com/repos/{owner}/{repo}"

    async with httpx.AsyncClient(
        follow_redirects=True
    ) as client:
        response = await client.get(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "DevPilot",
            },
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
    url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/HEAD?recursive=1"

    async with httpx.AsyncClient(
        follow_redirects=True
    ) as client:
        response = await client.get(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "DevPilot",
            },
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
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"

    async with httpx.AsyncClient(
        follow_redirects=True
    ) as client:
        response = await client.get(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "DevPilot",
            },
        )

    if response.status_code != 200:
        return None

    return response.json()