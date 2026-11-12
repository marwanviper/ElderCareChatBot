from sqlalchemy.orm import Session

from src.models.conversation import Conversation
from src.models.message import Message
from src.schemas.chat import (
    ConversationCreate,
    ConversationUpdate,
    MessageCreate,
)


def create_conversation(
    db: Session, conv_data: ConversationCreate
) -> Conversation:
    """Create a new conversation session for a resident."""
    new_conv = Conversation(
        resident_id=conv_data.resident_id,
        user_id=conv_data.user_id,
        title=conv_data.title,
        status=conv_data.status,
        extra_metadata=conv_data.extra_metadata,
    )
    db.add(new_conv)
    db.commit()
    db.refresh(new_conv)
    return new_conv


def get_conversation_by_id(
    db: Session, conversation_id: int
) -> Conversation | None:
    """Retrieve a conversation session by its ID."""
    return (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id)
        .first()
    )


def get_conversations_by_resident(
    db: Session,
    resident_id: int,
    skip: int = 0,
    limit: int = 50,
    status: str | None = None,
) -> list[Conversation]:
    """Retrieve all conversations for a specific resident, optionally filtered by status."""
    query = db.query(Conversation).filter(
        Conversation.resident_id == resident_id
    )
    if status is not None:
        query = query.filter(Conversation.status == status)

    return (
        query.order_by(Conversation.updated_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_conversation(
    db: Session, conversation_id: int, conv_data: ConversationUpdate
) -> Conversation | None:
    """Update conversation properties (title, status, extra_metadata)."""
    conv = get_conversation_by_id(db, conversation_id)
    if not conv:
        return None

    update_dict = conv_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(conv, key, value)

    db.commit()
    db.refresh(conv)
    return conv


def delete_conversation(db: Session, conversation_id: int) -> bool:
    """Delete a conversation and cascade-delete its messages."""
    conv = get_conversation_by_id(db, conversation_id)
    if conv:
        db.delete(conv)
        db.commit()
        return True
    return False


def create_message(
    db: Session, conversation_id: int, msg_data: MessageCreate
) -> Message:
    """Append a new message turn to a conversation and update conversation timestamp."""
    new_msg = Message(
        conversation_id=conversation_id,
        role=msg_data.role,
        content=msg_data.content,
        token_count=msg_data.token_count,
        extra_metadata=msg_data.extra_metadata,
    )
    db.add(new_msg)

    # Touch conversation updated_at
    conv = get_conversation_by_id(db, conversation_id)
    if conv:
        from utils.utils import _utcnow

        conv.updated_at = _utcnow()

    db.commit()
    db.refresh(new_msg)
    return new_msg


def get_messages_by_conversation(
    db: Session, conversation_id: int, skip: int = 0, limit: int = 100
) -> list[Message]:
    """Retrieve messages for a conversation ordered chronologically."""
    return (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def delete_message(db: Session, message_id: int) -> bool:
    """Delete a single message by ID."""
    msg = db.query(Message).filter(Message.id == message_id).first()
    if msg:
        db.delete(msg)
        db.commit()
        return True
    return False

