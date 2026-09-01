import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


async def explain_code(
    owner: str,
    repo: str,
    file_path: str,
    code: str,
):
    prompt = f"""
You are DevPilot, an AI software engineer.

You are analyzing this file from the GitHub repository:
{owner}/{repo}

File:
{file_path}

CODE START
{code}
CODE END

Explain this code clearly and practically.

Structure your response using these sections:

## Purpose
Explain what this code is responsible for.

## How It Works
Explain the important execution flow step by step.

## Key Components
Identify important functions, classes, variables, or modules.

## Dependencies
Explain important external or internal dependencies visible in the code.

## Potential Issues
Mention bugs, risks, confusing parts, or maintainability concerns only
when they are supported by the provided code.

Important rules:

- Base your explanation ONLY on the provided code.
- Do not invent functionality that is not present.
- If the code is incomplete, explicitly say so.
- Reference specific functions or sections when useful.
- Keep the explanation understandable to a developer.
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt,
    )

    return response.text