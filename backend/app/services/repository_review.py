import base64
import json

from app.core.gemini_client import get_gemini_client

from app.services.github_service import (
    get_repository_tree,
    get_file_content,
)


MODEL_NAME = "gemini-3.6-flash"

MAX_FILE_CHARS = 30000
MAX_FILES = 40


IGNORED_DIRECTORIES = {
    "node_modules",
    ".git",
    "dist",
    "build",
    "__pycache__",
    ".venv",
    "venv",
}


SOURCE_EXTENSIONS = {
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
}


def is_source_file(path: str) -> bool:
    parts = path.split("/")

    if any(
        directory in IGNORED_DIRECTORIES
        for directory in parts
    ):
        return False

    return any(
        path.lower().endswith(extension)
        for extension in SOURCE_EXTENSIONS
    )


async def build_repository_context(
    owner: str,
    repo: str,
):
    tree = await get_repository_tree(
        owner,
        repo,
    )

    if not tree:
        return None

    files = tree.get("tree", [])

    source_files = [
        item["path"]
        for item in files
        if item.get("type") == "blob"
        and is_source_file(
            item.get("path", "")
        )
    ]

    source_files = source_files[:MAX_FILES]

    context_parts = []

    for path in source_files:
        file_data = await get_file_content(
            owner,
            repo,
            path,
        )

        if not file_data:
            continue

        content = file_data.get("content")

        if not content:
            continue

        try:
            decoded = base64.b64decode(
                content
            ).decode(
                "utf-8",
                errors="ignore",
            )

        except Exception as exc:
            print(
                f"Failed to decode {path}:",
                exc,
            )
            continue

        truncated = False

        if len(decoded) > MAX_FILE_CHARS:
            decoded = (
                decoded[:MAX_FILE_CHARS]
                + "\n\n"
                "[FILE TRUNCATED FOR REVIEW]"
            )

            truncated = True

        file_header = f"FILE: {path}"

        if truncated:
            file_header += (
                "\nNOTE: This file was truncated. "
                "Do not report syntax errors caused "
                "only by the truncation."
            )

        context_parts.append(
            f"{file_header}\n{decoded}"
        )

    if not context_parts:
        return None

    return "\n\n---\n\n".join(
        context_parts
    )


async def review_repository(
    owner: str,
    repo: str,
):
    context = await build_repository_context(
        owner,
        repo,
    )

    if not context:
        return None

    prompt = f"""
You are an expert software engineer performing
a code review of a GitHub repository.

Review the provided repository source code.

Look for real issues involving:

- bugs
- incorrect logic
- missing error handling
- security problems
- bad practices
- maintainability problems
- performance problems
- architectural issues

IMPORTANT RULES:

1. Only report issues that are supported by
   the code you were given.

2. Do not invent files, functions, or code.

3. Do not report a syntax error merely because
   a file was truncated in the review context.

4. Some large files may contain the marker:
   [FILE TRUNCATED FOR REVIEW]

   If you see this marker, do not assume the
   original file is syntactically invalid.

5. Line numbers must only be provided when they
   can be determined reliably from the provided
   source.

6. If you are uncertain whether something is a
   real issue, do not report it.

Return ONLY valid JSON.

Use exactly this structure:

{{
  "summary": "Short overall assessment",
  "findings": [
    {{
      "severity": "high",
      "title": "Short issue title",
      "description": "Clear explanation of the issue",
      "file_path": "path/to/file.py",
      "line_start": 1,
      "line_end": 5
    }}
  ]
}}

Severity must be exactly one of:

high
medium
low

If line numbers cannot be determined reliably,
use null for line_start and line_end.

Do not include markdown.

Do not include ```json.

Do not include explanations outside the JSON.

Repository source code:

{context}
"""

    try:
        client = get_gemini_client()

        response = await client.aio.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
        )

        text = response.text.strip()

        if text.startswith("```"):
            text = text.replace(
                "```json",
                "",
                1,
            ).replace(
                "```",
                "",
                1,
            ).strip()

        result = json.loads(text)

        if not isinstance(result, dict):
            print(
                "Repository review returned "
                "an unexpected format."
            )
            return None

        if "summary" not in result:
            result["summary"] = (
                "No overall summary was provided."
            )

        if "findings" not in result:
            result["findings"] = []

        return result

    except json.JSONDecodeError as exc:
        print(
            "Repository review returned "
            "invalid JSON:",
            exc,
        )
        return None

    except Exception as exc:
        print(
            "Repository review failed:",
            exc,
        )
        return None