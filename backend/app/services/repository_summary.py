import asyncio
import traceback
from base64 import b64decode

from app.services.github_service import (
    get_repository_tree,
    get_file_content,
)
from app.services.ai_service import client


def is_important_file(path: str) -> bool:
    path_lower = path.lower()

    important_names = (
        "readme.md",
        "package.json",
        "requirements.txt",
        "pyproject.toml",
        "cargo.toml",
        "go.mod",
        "pom.xml",
        "build.gradle",
        "dockerfile",
        "docker-compose.yml",
        "docker-compose.yaml",
        "main.py",
        "app.py",
        "server.py",
        "index.py",
        "index.ts",
        "index.tsx",
        "index.js",
        "index.jsx",
        "vite.config.ts",
        "vite.config.js",
        "next.config.js",
        "next.config.ts",
    )

    if path_lower.endswith(important_names):
        return True

    important_directories = (
        "/api/",
        "/services/",
        "/components/",
        "/pages/",
        "/routes/",
        "/models/",
        "/schemas/",
        "/controllers/",
        "/utils/",
        "/lib/",
        "/core/",
    )

    return any(
        directory in path_lower
        for directory in important_directories
    )


def is_supported_source_file(path: str) -> bool:
    path_lower = path.lower()

    supported_extensions = (
        ".py",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".java",
        ".go",
        ".rs",
        ".cpp",
        ".c",
        ".cs",
        ".rb",
        ".php",
        ".swift",
        ".kt",
        ".html",
        ".css",
        ".json",
        ".yaml",
        ".yml",
        ".md",
    )

    return path_lower.endswith(supported_extensions)


async def fetch_file_context(
    owner: str,
    repo: str,
    item: dict,
):
    file_path = item.get("path", "")

    if any(
        ignored in file_path.lower()
        for ignored in (
            "node_modules/",
            ".git/",
            "dist/",
            "build/",
            "__pycache__/",
            ".next/",
            "coverage/",
        )
    ):
        return None

    try:
        file = await get_file_content(
            owner,
            repo,
            file_path,
        )

        if not file or "content" not in file:
            return None

        decoded = b64decode(
            file["content"]
        ).decode(
            "utf-8",
            errors="ignore",
        )

        return f"""
FILE:
{file_path}

CONTENT:
{decoded[:4000]}
"""

    except Exception:
        return None


async def summarize_repository(owner: str, repo: str):
    tree = await get_repository_tree(
        owner,
        repo,
    )

    if tree is None:
        return "Repository not found."

    repository_tree = tree.get(
        "tree",
        [],
    )

    # Build a compact representation
    # of the repository structure.
    tree_lines = []

    for item in repository_tree:
        path = item.get("path", "")
        item_type = item.get("type", "")

        if item_type == "tree":
            tree_lines.append(
                f"[DIR]  {path}"
            )

        elif item_type == "blob":
            tree_lines.append(
                f"[FILE] {path}"
            )

    tree_context = "\n".join(
        tree_lines[:500]
    )

    # Select source files that are useful
    # for understanding the architecture.
    files_to_analyze = [
        item
        for item in repository_tree
        if item.get("type") == "blob"
        and is_supported_source_file(
            item.get("path", "")
        )
    ]

    files_to_analyze.sort(
        key=lambda item: (
            not is_important_file(
                item.get("path", "")
            ),
            item.get("path", ""),
        )
    )

    selected_files = files_to_analyze[:10]

    # Fetch files concurrently instead of
    # waiting for each GitHub request sequentially.
    results = await asyncio.gather(
        *[
            fetch_file_context(
                owner,
                repo,
                item,
            )
            for item in selected_files
        ]
    )

    files = [
        result
        for result in results
        if result
    ]

    prompt = f"""
You are a senior software architect performing a technical analysis of a GitHub repository.

Analyze the repository using BOTH:

1. The repository structure.
2. The selected source files.

Do not invent files, technologies, architecture, or behavior that is not supported by the provided context.

If something cannot be determined from the available files, explicitly say that it could not be determined.

Return ONLY valid Markdown.

Use EXACTLY this structure:

# 🚀 Project Overview

Explain what the project does and what problem it appears to solve.

# 🏗 Architecture

Describe the application's architecture and how the major parts appear to interact.

# 📂 Folder Structure

Explain the important directories and files based on the actual repository tree.

# ⚙️ Tech Stack

Identify the technologies, languages, frameworks, libraries, and infrastructure that can be confirmed from the repository.

# 🔑 Main Components

Explain the major modules, services, components, APIs, or other important pieces.

# 🔄 Application Flow

Describe the likely flow of data through the application, from entry point to major operations.

# ▶ Entry Point

Identify the application's entry point or explain why it cannot be determined.

# ✅ Strengths

List concrete strengths visible in the repository.

# ⚠️ Weaknesses

List concrete weaknesses, risks, or areas that appear underdeveloped.

# 💡 Suggested Improvements

Suggest practical improvements for:

- Maintainability
- Performance
- Scalability
- Developer Experience
- Security

Only make recommendations that are relevant to the repository.

Repository Structure:

{tree_context}

Selected Repository Files:

{''.join(files)}
"""

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
        )

        return response.text

    except Exception:
        print("\n" + "=" * 80)
        print("Gemini Request Failed")
        traceback.print_exc()
        print("=" * 80 + "\n")

        return (
            "⚠️ Gemini is temporarily unavailable.\n\n"
            "Please try analyzing the repository again "
            "in a moment."
        )