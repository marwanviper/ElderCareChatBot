from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base
from utils.utils import _utcnow

if TYPE_CHECKING:
    from src.models.conversation import Conversation


class MessageRole(str, Enum):
    """Permitted roles for chat conversation turns."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

    def __str__(self) -> str:
        return self.value


class Message(Base):
    """SQLAlchemy model representing the messages table."""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    conversation_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[MessageRole] = mapped_column(
        SQLEnum(
            MessageRole,
            native_enum=False,
            length=20,
            values_callable=lambda obj: [e.value for e in obj],
            validate_strings=True,
        ),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, nullable=False, index=True
    )
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )

    # Relationships
    conversation: Mapped["Conversation"] = relationship(
        "Conversation", back_populates="messages"
    )

    __table_args__ = (
        Index("ix_messages_conv_created", "conversation_id", "created_at"),
    )

