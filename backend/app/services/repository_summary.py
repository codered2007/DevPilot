import asyncio
import traceback
from base64 import b64decode

from app.services.github_service import (
    get_repository_tree,
    get_file_content,
)
from app.services.ai_service import client


async def summarize_repository(owner: str, repo: str):
    tree = await get_repository_tree(owner, repo)

    if tree is None:
        return "Repository not found."

    files = []

    important_files = sorted(
        tree["tree"],
        key=lambda item: (
            not (
                item["path"].lower().endswith(
                    (
                        "readme.md",
                        "package.json",
                        "requirements.txt",
                        "pyproject.toml",
                        "main.py",
                        "app.py",
                        "index.ts",
                        "index.tsx",
                        "index.js",
                        "index.jsx",
                    )
                )
            ),
            item["path"],
        ),
    )

    for item in important_files:
        if item["type"] != "blob":
            continue

        if len(files) >= 5:
            break

        file = await get_file_content(
            owner,
            repo,
            item["path"],
        )

        if file and "content" in file:
            try:
                decoded = b64decode(
                    file["content"]
                ).decode(
                    "utf-8",
                    errors="ignore",
                )

                files.append(
                    f"""
FILE:
{item["path"]}

CONTENT:
{decoded[:2000]}
"""
                )

            except Exception:
                continue

    prompt = f"""
You are a senior software architect.

Analyze this GitHub repository.

Return ONLY valid Markdown.

Use EXACTLY this format:

# 🚀 Project Overview

Explain what this project does.

# 🏗 Architecture

Describe the overall architecture.

# 📂 Folder Structure

Explain the important folders and files.

# ⚙️ Tech Stack

List the technologies and frameworks used.

# 🔑 Main Components

Explain the major modules, services and components.

# ▶ Entry Point

Identify the application's entry point.

# ✅ Strengths

List the strengths.

# ⚠️ Weaknesses

List the weaknesses.

# 💡 Suggested Improvements

Suggest practical improvements for:
- Maintainability
- Performance
- Scalability
- Developer Experience

Repository:

{''.join(files)}
"""

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash-001",
                contents=prompt,
            )

            return response.text

        except Exception:
            print("\n" + "=" * 80)
            print(f"Gemini Request Failed (Attempt {attempt + 1})")
            traceback.print_exc()
            print("=" * 80 + "\n")

            if attempt < 2:
                await asyncio.sleep(2)

    return (
        "⚠️ Unable to analyze the repository.\n\n"
        "Please check the backend logs for the full Gemini error."
    )