import os
from base64 import b64decode

from dotenv import load_dotenv
from google import genai

from app.services.github_service import (
    search_repository_with_content,
)

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


async def ask_ai(
    owner: str,
    repo: str,
    message: str,
):
    matches = await search_repository_with_content(
        owner,
        repo,
        message,
    )

    context_parts = []
    context_length = 0

    MAX_CONTEXT_LENGTH = 40000
    MAX_FILE_LENGTH = 10000

    for match in matches[:8]:
        raw_content = match.get(
            "content",
            "",
        )

        try:
            decoded_content = b64decode(
                raw_content
            ).decode(
                "utf-8",
                errors="ignore",
            )
        except Exception:
            decoded_content = raw_content

        if not decoded_content.strip():
            continue

        remaining = (
            MAX_CONTEXT_LENGTH - context_length
        )

        if remaining <= 0:
            break

        file_content = decoded_content[
            :min(
                MAX_FILE_LENGTH,
                remaining,
            )
        ]

        context_parts.append(
            f"FILE: {match['path']}\n\n"
            f"{file_content}"
        )

        context_length += len(file_content)

    context = "\n\n---\n\n".join(
        context_parts
    )

    if not context:
        context = (
            "No relevant repository files "
            "could be retrieved."
        )

    prompt = f"""
You are DevPilot, an AI software engineer.

You are analyzing the GitHub repository:
{owner}/{repo}

Use ONLY the repository context provided below when making
claims about the repository's implementation.

Repository Context:

{context}

User Question:

{message}

Instructions:

- Give a clear and practical answer.
- Reference specific files when useful.
- Explain your reasoning from the available code.
- If the available repository context is insufficient,
  explicitly say what information is missing.
- Do not invent files, features, technologies, or behavior
  that are not supported by the repository context.
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt,
    )

    return response.text