import base64
import json

from app.core.gemini_client import get_gemini_client
from app.services.github_service import (
    get_file_content,
    get_repository_tree,
)


MODEL_NAMES = [
    "gemini-3.6-flash",
    "gemini-3.5-flash",
]

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


def should_include_file(path: str) -> bool:
    """
    Decide whether a repository file should be included
    in the AI review context.
    """

    parts = path.split("/")

    for part in parts:
        if part.lower() in IGNORED_DIRECTORIES:
            return False

    path_lower = path.lower()

    return any(
        path_lower.endswith(extension)
        for extension in SOURCE_EXTENSIONS
    )


async def build_repository_context(
    owner: str,
    repo: str,
):
    """
    Build a repository context for the AI reviewer.

    Returns:
        tuple[str, list[str]]:
            - repository context
            - files whose contents could not be retrieved
    """

    tree = await get_repository_tree(
        owner,
        repo,
    )

    if not tree:
        return "", []

    files = tree.get(
        "tree",
        [],
    )

    source_files = [
        item
        for item in files
        if item.get("type") == "blob"
        and should_include_file(
            item.get("path", "")
        )
    ]

    source_files = source_files[:MAX_FILES]

    context_parts = []
    unavailable_files = []

    for item in source_files:
        path = item.get(
            "path",
            "",
        )

        try:
            file_data = await get_file_content(
                owner,
                repo,
                path,
            )
        except Exception as exc:
            print(
                f"GitHub file request failed: "
                f"{path} — {type(exc).__name__}: {exc}"
            )

            unavailable_files.append(path)
            continue

        if not file_data:
            unavailable_files.append(path)
            continue

        encoded_content = file_data.get(
            "content",
            "",
        )

        if not encoded_content:
            unavailable_files.append(path)
            continue

        try:
            decoded = base64.b64decode(
                encoded_content
            ).decode(
                "utf-8",
                errors="ignore",
            )
        except Exception as exc:
            print(
                f"Unable to decode file: "
                f"{path} — {exc}"
            )

            unavailable_files.append(path)
            continue

        if not decoded.strip():
            unavailable_files.append(path)
            continue

        truncated = False

        if len(decoded) > MAX_FILE_CHARS:
            decoded = (
                decoded[:MAX_FILE_CHARS]
            )
            truncated = True

        file_header = f"FILE: {path}"

        if truncated:
            file_header += (
                "\nNOTE: This file was truncated "
                f"to {MAX_FILE_CHARS} characters."
            )

        context_parts.append(
            f"{file_header}\n"
            "```text\n"
            f"{decoded}\n"
            "```"
        )

    context = "\n\n---\n\n".join(
        context_parts
    )

    return (
        context,
        unavailable_files,
    )


async def review_repository(
    owner: str,
    repo: str,
):
    """
    Analyze a GitHub repository and return
    structured code-review findings.
    """

    context, unavailable_files = (
        await build_repository_context(
            owner,
            repo,
        )
    )

    if not context:
        print(
            "Repository review has no "
            "available source files."
        )

        return None

    unavailable_section = (
        "\n".join(
            f"- {path}"
            for path in unavailable_files
        )
        if unavailable_files
        else "None"
    )

    prompt = f"""
You are an expert software engineer performing
a code review of a GitHub repository.

Your job is to identify real, actionable,
evidence-based problems in the provided source code.

Repository:
{owner}/{repo}

IMPORTANT RULES:

1. Only report issues that are supported by
   the provided repository content.

2. The repository tree may contain files whose
   contents could not be retrieved.

3. The following files were unavailable:

{unavailable_section}

4. NEVER claim that an unavailable file does
   not exist.

5. NEVER infer the contents, imports, functions,
   classes, routes, behavior, or dependencies
   of an unavailable file.

6. Do not report an issue that depends on the
   contents of an unavailable file.

7. Do not assume that a file is missing merely
   because it is not included in the provided
   source context.

8. Do not report syntax errors caused by the
   review context being truncated.

9. Only provide line numbers when they can be
   determined reliably from the provided code.

10. If you are uncertain whether something is
    actually a problem, do not report it.

11. Focus on meaningful engineering issues such as:
    - bugs
    - incorrect logic
    - security problems
    - broken API usage
    - incorrect async/sync behavior
    - data handling problems
    - error handling problems
    - performance problems
    - reliability issues
    - maintainability issues

12. Do not report stylistic preferences as bugs.

13. Do not invent runtime behavior.

14. Do not assume external configuration values
    unless they are visible in the repository.

15. Do not duplicate the same issue across
    multiple findings.

16. Findings must refer only to files whose
    contents are actually present below.

Return ONLY valid JSON.

The JSON must have this structure:

{{
  "summary": "Short overall assessment of the repository.",
  "findings": [
    {{
      "severity": "HIGH",
      "title": "Short issue title",
      "description": "Clear explanation of the problem.",
      "file_path": "path/to/file.py",
      "line_start": 10,
      "line_end": 20,
      "recommendation": "Specific recommendation for fixing it."
    }}
  ]
}}

Allowed severity values:

- HIGH
- MEDIUM
- LOW

If no meaningful issues are found, return:

{{
  "summary": "No significant issues were identified from the available source files.",
  "findings": []
}}

Repository source:

{context}
"""

    try:
        client = get_gemini_client()
        response = None
        for model_name in MODEL_NAMES:
            try:
                print(
                    f"Trying Gemini model: {model_name}"
                )
                response = await client.aio.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                print(
                    f"Gemini review succeeded with: "
                    f"{model_name}"
                )
                break
            except Exception as exc:
                print(
                    f"Gemini model failed: "
                    f"{model_name} — {exc}"
                )
        if response is None:
            raise RuntimeError(
                "All Gemini review models are currently unavailable."
            )

        text = response.text.strip()

        if text.startswith("```"):
            text = text.replace(
                "```json",
                "",
                1,
            )

            text = text.replace(
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

        if not isinstance(
            result["findings"],
            list,
        ):
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