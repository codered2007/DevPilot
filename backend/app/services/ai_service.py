import os
from base64 import b64decode

from dotenv import load_dotenv
from google import genai

from app.services.github_service import (
    search_repository,
    get_file_content,
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
    matches = await search_repository(
        owner,
        repo,
        message,
    )

    context = ""

    for match in matches[:5]:
        file = await get_file_content(
            owner,
            repo,
            match["path"],
        )

        if not file:
            continue

        raw_content = file.get("content", "")

        try:
            decoded_content = b64decode(
                raw_content
            ).decode(
                "utf-8",
                errors="ignore",
            )
        except Exception:
            decoded_content = raw_content

        context += (
            f"\n\nFILE: {match['path']}\n\n"
            f"{decoded_content[:12000]}"
        )

    prompt = f"""
You are DevPilot, an AI software engineer.

Use the repository context below to answer the user's question.

Give a clear, practical answer based on the available repository code.
If the repository context does not contain enough information to answer,
say so instead of inventing details.

Repository Context:

{context}

Question:

{message}
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt,
    )

    return response.text