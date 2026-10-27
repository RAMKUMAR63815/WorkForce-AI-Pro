
from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import or_, select, update

from app.api.rbac import AuthenticatedUser, DbSession
from app.models.chat import ChatConversation, ChatMessage
from app.models.user import User
from app.schemas.chat import (
    ConversationCreate,
    ConversationResponse,
    MessageCreate,
    MessageResponse,
)

router = APIRouter(prefix="/chat", tags=["One-to-One Chat"])


def get_conversation_for_user(
    db: DbSession,
    conversation_id: int,
    user_id: int,
) -> ChatConversation:
    conversation = db.get(ChatConversation, conversation_id)

    if conversation is None:
        raise HTTPException(404, "Conversation not found.")

    if user_id not in (
        conversation.user_one_id,
        conversation.user_two_id,
    ):
        raise HTTPException(403, "You cannot access this conversation.")

    return conversation


@router.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_conversation(
    payload: ConversationCreate,
    db: DbSession,
    current_user: AuthenticatedUser,
):
    if payload.recipient_id == current_user.id:
        raise HTTPException(400, "You cannot chat with yourself.")

    recipient = db.get(User, payload.recipient_id)

    if recipient is None or not recipient.is_active:
        raise HTTPException(404, "Active recipient not found.")

    first_id, second_id = sorted(
        [current_user.id, payload.recipient_id]
    )

    existing = db.scalar(
        select(ChatConversation).where(
            ChatConversation.user_one_id == first_id,
            ChatConversation.user_two_id == second_id,
        )
    )

    if existing:
        return existing

    conversation = ChatConversation(
        user_one_id=first_id,
        user_two_id=second_id,
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return conversation


@router.get(
    "/conversations",
    response_model=list[ConversationResponse],
)
def list_conversations(
    db: DbSession,
    current_user: AuthenticatedUser,
):
    return db.scalars(
        select(ChatConversation)
        .where(
            or_(
                ChatConversation.user_one_id == current_user.id,
                ChatConversation.user_two_id == current_user.id,
            )
        )
        .order_by(ChatConversation.created_at.desc())
    ).all()


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def send_message(
    conversation_id: int,
    payload: MessageCreate,
    db: DbSession,
    current_user: AuthenticatedUser,
):
    get_conversation_for_user(
        db, conversation_id, current_user.id
    )

    message = ChatMessage(
        conversation_id=conversation_id,
        sender_id=current_user.id,
        message=payload.message.strip(),
    )

    if not message.message:
        raise HTTPException(400, "Message cannot be empty.")

    db.add(message)
    db.commit()
    db.refresh(message)

    return message


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=list[MessageResponse],
)
def get_messages(
    conversation_id: int,
    db: DbSession,
    current_user: AuthenticatedUser,
):
    get_conversation_for_user(
        db, conversation_id, current_user.id
    )

    return db.scalars(
        select(ChatMessage)
        .where(ChatMessage.conversation_id == conversation_id)
        .order_by(ChatMessage.sent_at.asc())
        .limit(500)
    ).all()


@router.post("/conversations/{conversation_id}/read")
def mark_messages_as_read(
    conversation_id: int,
    db: DbSession,
    current_user: AuthenticatedUser,
):
    get_conversation_for_user(
        db, conversation_id, current_user.id
    )

    db.execute(
        update(ChatMessage)
        .where(
            ChatMessage.conversation_id == conversation_id,
            ChatMessage.sender_id != current_user.id,
            ChatMessage.read_at.is_(None),
        )
        .values(read_at=datetime.now())
    )
    db.commit()

    return {"message": "Messages marked as read."}
