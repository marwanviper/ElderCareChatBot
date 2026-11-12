from datetime import datetime
from typing import TYPE_CHECKING, Any, List

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base
from utils.utils import _utcnow

if TYPE_CHECKING:
    from src.models.message import Message
    from src.models.resident import Resident
    from src.models.user import User


class Conversation(Base):
    """SQLAlchemy model representing the conversations table."""

    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    resident_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("residents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(
        String(30), default="active", nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow, nullable=False
    )
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )

    # Relationships
    resident: Mapped["Resident"] = relationship(
        "Resident", back_populates="conversations"
    )
    user: Mapped["User | None"] = relationship(
        "User", back_populates="conversations"
    )
    messages: Mapped[List["Message"]] = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )

