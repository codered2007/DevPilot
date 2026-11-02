
from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import get_current_session
from app.api.repositories import get_accessible_repository
from app.database import (
    create_conversation,
    list_conversations,
    get_conversation,
    get_conversation_messages,
    add_conversation_message,
    delete_conversation,
)
from app.schemas.chat import ChatMessage, ChatRequest
from app.services.ai_service import ask_ai


router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


def get_user_id(session: dict) -> int:
    """Extract and validate the authenticated GitHub user ID."""

    user_id = session.get("github_user", {}).get("id")

    if not isinstance(user_id, int) or isinstance(user_id, bool):
        raise HTTPException(
            status_code=401,
            detail="Invalid user identity. Please sign in again.",
        )

    return user_id


async def verify_repository_access(
    owner: str,
    repo: str,
    session: dict,
):
    """Verify repository access using the authenticated GitHub token."""

    token = session.get("access_token")

    if not token:
        raise HTTPException(
            status_code=401,
            detail="GitHub access token is missing. Please sign in again.",
        )

    await get_accessible_repository(
        owner,
        repo,
        token,
    )


def verify_conversation(
    conversation_id: str,
    user_id: int,
    owner: str,
    repo: str,
):
    """Verify conversation ownership and repository association."""

    conversation = get_conversation(
        conversation_id,
        user_id,
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    if (
        conversation["owner"].lower() != owner.lower()
        or conversation["repo"].lower() != repo.lower()
    ):
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    return conversation


@router.post("/conversations")
async def create_new_conversation(
    owner: str,
    repo: str,
    session: dict = Depends(get_current_session),
):
    user_id = get_user_id(session)

    await verify_repository_access(
        owner,
        repo,
        session,
    )

    conversation = create_conversation(
        user_id,
        owner,
        repo,
    )

    return {"conversation": conversation}


@router.get("/conversations")
async def get_conversations(
    owner: str,
    repo: str,
    session: dict = Depends(get_current_session),
):
    user_id = get_user_id(session)

    await verify_repository_access(
        owner,
        repo,
        session,
    )

    conversations = list_conversations(
        user_id,
        owner,
        repo,
    )

    return {"conversations": conversations}


@router.get("/conversations/{conversation_id}")
async def get_conversation_history(
    conversation_id: str,
    owner: str,
    repo: str,
    session: dict = Depends(get_current_session),
):
    user_id = get_user_id(session)

    await verify_repository_access(
        owner,
        repo,
        session,
    )

    verify_conversation(
        conversation_id,
        user_id,
        owner,
        repo,
    )

    messages = get_conversation_messages(
        conversation_id,
        user_id,
    )

    return {
        "conversation_id": conversation_id,
        "messages": messages,
    }


@router.delete("/conversations/{conversation_id}")
async def remove_conversation(
    conversation_id: str,
    owner: str,
    repo: str,
    session: dict = Depends(get_current_session),
):
    user_id = get_user_id(session)

    await verify_repository_access(
        owner,
        repo,
        session,
    )

    verify_conversation(
        conversation_id,
        user_id,
        owner,
        repo,
    )

    delete_conversation(
        conversation_id,
        user_id,
    )

    return {"message": "Conversation deleted."}


@router.post("/")
async def chat(
    request: ChatRequest,
    session: dict = Depends(get_current_session),
):
    user_id = get_user_id(session)

    await verify_repository_access(
        request.owner,
        request.repo,
        session,
    )

    if not request.conversation_id:
        raise HTTPException(
            status_code=400,
            detail="A conversation ID is required.",
        )

    verify_conversation(
        request.conversation_id,
        user_id,
        request.owner,
        request.repo,
    )

    add_conversation_message(
        request.conversation_id,
        "user",
        request.message,
    )

    stored_messages = get_conversation_messages(
        request.conversation_id,
        user_id,
    )

    history = [
    ChatMessage(
        role=message["role"],
        content=message["content"],
    )
    for message in stored_messages[:-1]
]

    response = await ask_ai(
        request.owner,
        request.repo,
        request.message,
        history,
        user_id=user_id,
    )

    add_conversation_message(
        request.conversation_id,
        "assistant",
        response["response"],
        sources=response.get("sources", []),
    )

    return {
        **response,
        "conversation_id": request.conversation_id,
    }
