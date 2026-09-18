import os
from app.core.gemini_client import get_gemini_client

from app.services.vector_store import (
    search_code,
)





async def ask_ai(
    owner: str,
    repo: str,
    message: str,
    history: list,
):
    # Use the current user question for retrieval.
    # Conversation history is handled separately by Gemini.
    matches = search_code(
        owner,
        repo,
        message,
        limit=8,
    )

    context_parts = []
    context_length = 0
    source_files = []

    MAX_CONTEXT_LENGTH = 40000
    MAX_CHUNK_LENGTH = 10000

    for match in matches:
        content = match.get(
            "content",
            "",
        )

        if not content.strip():
            continue

        remaining = (
            MAX_CONTEXT_LENGTH - context_length
        )

        if remaining <= 0:
            break

        chunk_content = content[
            :min(
                MAX_CHUNK_LENGTH,
                remaining,
            )
        ]

        start_line = match.get(
            "start_line"
        )

        end_line = match.get(
            "end_line"
        )

        if (
            start_line is not None
            and end_line is not None
        ):
            file_label = (
                f"FILE: {match['path']} "
                f"(lines {start_line}-{end_line})"
            )
        else:
            file_label = (
                f"FILE: {match['path']}"
            )

        context_parts.append(
            f"{file_label}\n\n"
            f"{chunk_content}"
        )

        if match["path"] not in source_files:
            source_files.append(
                match["path"]
            )

        context_length += len(
            chunk_content
        )

    context = "\n\n---\n\n".join(
        context_parts
    )

    if not context:
        context = (
            "No relevant repository files "
            "could be retrieved from the "
            "semantic code index."
        )

    conversation = "\n\n".join(
        f"{item.role.upper()}: {item.content}"
        for item in history
    )

    prompt = f"""
You are DevPilot, an AI software engineer.

You are analyzing the GitHub repository:
{owner}/{repo}

Use ONLY the repository context provided below when making
claims about the repository's implementation.

Repository Context:

{context}

Conversation History:

{conversation}

Current User Question:

{message}

Instructions:

- Give a clear and practical answer.
- Use the conversation history to understand follow-up questions
  and references such as "it", "that", or "where is this used?".
- Use the repository context to answer questions about the code.
- Reference specific files when useful.
- When line ranges are provided, use them when explaining
  where an implementation is located.
- Explain your reasoning from the available code.
- If the available repository context is insufficient,
  explicitly say what information is missing.
- Do not invent files, features, technologies, or behavior
  that are not supported by the repository context.
"""
    client = get_gemini_client()
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt,
    )

    return {
        "response": response.text,
        "sources": source_files,
    }