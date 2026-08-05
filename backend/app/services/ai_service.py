import os

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

        if file:
            context += (
                f"\n\nFILE: {match['path']}\n\n"
                f"{file.get('content', '')[:12000]}"
            )

    prompt = f"""
You are DevPilot, an AI software engineer.

Use the repository context below to answer.

Repository Context:

{context}

Question:

{message}
"""

    response = client.models.generate_content(
        model="gemini-flash-latest",
        contents=prompt,
    )

    return response.text