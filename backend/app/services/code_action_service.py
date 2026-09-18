from app.core.gemini_client import get_gemini_client

from app.services.vector_store import search_code


ACTION_INSTRUCTIONS = {
    "fix": (
        "Identify the most likely bug or correctness issue "
        "in the provided code. Return a corrected version "
        "of the code. Preserve the existing behavior "
        "wherever possible."
    ),
    "improve": (
        "Improve the provided code for readability, "
        "maintainability, robustness, and code quality. "
        "Do not change its intended behavior. Return "
        "the improved version of the code."
    ),
    "refactor": (
        "Refactor the provided code to improve its structure "
        "and maintainability. Preserve its intended behavior "
        "and public interfaces wherever possible. Return "
        "the refactored version of the code."
    ),
}


async def generate_code_action(
    owner: str,
    repo: str,
    file_path: str,
    code: str,
    action: str,
):
    matches = search_code(
        owner,
        repo,
        code,
        limit=5,
    )

    context_parts = []

    for match in matches:
        content = match.get(
            "content",
            "",
        )

        if not content.strip():
            continue

        context_parts.append(
            f"FILE: {match['path']}\n\n"
            f"{content}"
        )

    context = "\n\n---\n\n".join(
        context_parts
    )

    if not context:
        context = (
            "No additional repository context "
            "was found."
        )

    instruction = ACTION_INSTRUCTIONS[action]

    prompt = f'''
You are DevPilot, an AI software engineer.

You are working on the GitHub repository:

{owner}/{repo}

The user wants to perform this code action:

{action}

Target file:

{file_path}

Target code:

{code}

Relevant repository context:

{context}

Task:

{instruction}

Important requirements:

- Return ONLY the complete modified code.
- Do not use Markdown code fences.
- Do not include explanations.
- Do not include comments about what you changed.
- Do not invent dependencies or APIs.
- Keep the result compatible with the surrounding repository code.
'''

    client = get_gemini_client()

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt,
    )

    return response.text.strip()