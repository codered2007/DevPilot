import ast
import base64
import json
import os
import re
import asyncio

from app.core.gemini_client import get_gemini_client
from app.services.github_service import (
    get_file_content,
    get_repository_tree,
)


MODEL_NAMES = [
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
]

MAX_FILES = 80
MAX_FILE_CHARS = 20000

MODEL_RETRIES = 2
RETRY_DELAY_SECONDS = 2


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
    parts = path.split("/")

    for part in parts:
        if part.lower() in IGNORED_DIRECTORIES:
            return False

    path_lower = path.lower()

    return any(
        path_lower.endswith(extension)
        for extension in SOURCE_EXTENSIONS
    )


def extract_python_imports(
    content: str,
) -> list[str]:
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return []

    imports = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)

    return sorted(set(imports))


def extract_javascript_imports(
    content: str,
) -> list[str]:
    patterns = [
        r'import\s+(?:.+?\s+from\s+)?["\']([^"\']+)["\']',
        r'import\s*\(\s*["\']([^"\']+)["\']\s*\)',
        r'require\s*\(\s*["\']([^"\']+)["\']\s*\)',
    ]

    imports = []

    for pattern in patterns:
        imports.extend(
            re.findall(
                pattern,
                content,
            )
        )

    return sorted(set(imports))


def extract_imports(
    path: str,
    content: str,
) -> list[str]:
    extension = os.path.splitext(
        path.lower()
    )[1]

    if extension == ".py":
        return extract_python_imports(
            content
        )

    if extension in {
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
    }:
        return extract_javascript_imports(
            content
        )

    return []


def build_dependency_context(
    files: list[dict],
) -> str:
    sections = []

    for file in files:
        path = file["path"]
        content = file["content"]

        imports = extract_imports(
            path,
            content,
        )

        imports_text = (
            "\n".join(
                f"- {item}"
                for item in imports
            )
            if imports
            else "- No imports detected"
        )

        sections.append(
            f"FILE: {path}\n"
            f"IMPORTS:\n"
            f"{imports_text}"
        )

    return "\n\n---\n\n".join(
        sections
    )


async def collect_repository_files(
    owner: str,
    repo: str,
):
    tree = await get_repository_tree(
        owner,
        repo,
    )

    if not tree:
        return [], []

    source_files = [
        item
        for item in tree.get(
            "tree",
            [],
        )
        if item.get("type") == "blob"
        and should_include_file(
            item.get("path", "")
        )
    ]

    source_files = source_files[:MAX_FILES]

    available_files = []
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
                f"Architecture file request failed: "
                f"{path} — "
                f"{type(exc).__name__}: {exc}"
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
                f"Unable to decode architecture file: "
                f"{path} — {exc}"
            )

            unavailable_files.append(path)
            continue

        if not decoded.strip():
            unavailable_files.append(path)
            continue

        if len(decoded) > MAX_FILE_CHARS:
            decoded = decoded[
                :MAX_FILE_CHARS
            ]

        available_files.append(
            {
                "path": path,
                "content": decoded,
            }
        )

    return (
        available_files,
        unavailable_files,
    )


def build_architecture_prompt(
    owner: str,
    repo: str,
    dependency_context: str,
    unavailable_files: list[str],
):
    unavailable_section = (
        "\n".join(
            f"- {path}"
            for path in unavailable_files
        )
        if unavailable_files
        else "None"
    )

    return f"""
You are an expert software architect.

Analyze the architecture of this GitHub repository.

Repository:
{owner}/{repo}

Your goal is to describe the repository's actual
architecture using only the evidence provided.

IMPORTANT RULES:

1. Only make claims supported by the provided
   repository information.

2. Some repository files may be unavailable.

3. These files were unavailable:

{unavailable_section}

4. NEVER infer the contents or dependencies of
   unavailable files.

5. Do not claim that an unavailable file does not
   exist.

6. Do not invent modules, services, routes,
   components, dependencies, or relationships.

7. Clearly distinguish detected dependencies from
   architectural observations.

8. If evidence is insufficient, omit the claim.

Return ONLY valid JSON.

Use exactly this structure:

{{
  "summary": "Short architectural summary.",
  "entry_points": [
    {{
      "file": "path/to/file",
      "reason": "Why this appears to be an entry point."
    }}
  ],
  "modules": [
    {{
      "name": "Module name",
      "paths": ["path/to/file"],
      "description": "What this module appears to contain."
    }}
  ],
  "dependencies": [
    {{
      "source": "path/to/source",
      "target": "path/to/target-or-module",
      "type": "import"
    }}
  ],
  "observations": [
    "Evidence-based architectural observation."
  ]
}}

Repository dependency information:

{dependency_context}
"""


async def generate_architecture_response(
    client,
    prompt: str,
):
    last_error = None

    for model_name in MODEL_NAMES:

        for attempt in range(
            MODEL_RETRIES + 1
        ):

            try:
                print(
                    f"Trying Gemini architecture model: "
                    f"{model_name} "
                    f"(attempt {attempt + 1}/{MODEL_RETRIES + 1})"
                )

                response = (
                    await client.aio.models.generate_content(
                        model=model_name,
                        contents=prompt,
                    )
                )

                print(
                    f"Gemini architecture analysis "
                    f"succeeded with: {model_name}"
                )

                return response

            except Exception as exc:
                last_error = exc

                print(
                    f"Gemini architecture model failed: "
                    f"{model_name} — {exc}"
                )

                error_text = str(exc)

                is_temporary_error = (
                    "503" in error_text
                    or "UNAVAILABLE" in error_text
                    or "429" in error_text
                    or "RESOURCE_EXHAUSTED" in error_text
                )

                if (
                    is_temporary_error
                    and attempt < MODEL_RETRIES
                ):
                    print(
                        f"Retrying {model_name} "
                        f"in {RETRY_DELAY_SECONDS} seconds..."
                    )

                    await asyncio.sleep(
                        RETRY_DELAY_SECONDS
                    )

                else:
                    break

    if last_error:
        raise RuntimeError(
            "All Gemini architecture models "
            "are currently unavailable."
        ) from last_error

    raise RuntimeError(
        "No Gemini architecture model "
        "was available."
    )


async def analyze_repository_architecture(
    owner: str,
    repo: str,
):
    files, unavailable_files = (
        await collect_repository_files(
            owner,
            repo,
        )
    )

    if not files:
        print(
            "Architecture analysis has no "
            "available source files."
        )

        return None

    dependency_context = (
        build_dependency_context(files)
    )

    prompt = build_architecture_prompt(
        owner,
        repo,
        dependency_context,
        unavailable_files,
    )

    try:
        client = get_gemini_client()

        response = (
            await generate_architecture_response(
                client,
                prompt,
            )
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
            return None

        result.setdefault(
            "summary",
            "No architectural summary was provided.",
        )

        result.setdefault(
            "entry_points",
            [],
        )

        result.setdefault(
            "modules",
            [],
        )

        result.setdefault(
            "dependencies",
            [],
        )

        result.setdefault(
            "observations",
            [],
        )

        result["unavailable_files"] = (
            unavailable_files
        )

        return result

    except json.JSONDecodeError as exc:
        print(
            "Architecture analysis returned "
            "invalid JSON:",
            exc,
        )

        return None

    except Exception as exc:
        print(
            "Repository architecture analysis failed:",
            exc,
        )

        return None