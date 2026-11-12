from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from src.models.message import MessageRole


class MessageBase(BaseModel):
    """Shared properties for a chat message."""

    role: MessageRole = Field(
        ...,
        description="Role of the message author: 'system', 'user', or 'assistant'",
        examples=["user"],
    )
    content: str = Field(
        ...,
        min_length=1,
        description="Textual content of the message",
        examples=["How are you feeling today?"],
    )
    token_count: int | None = Field(
        default=None,
        ge=0,
        description="Optional token count for usage tracking",
        examples=[12],
    )
    extra_metadata: dict[str, Any] | None = Field(
        default=None,
        description="Optional diagnostic and provenance metadata",
        examples=[{"model": "gemini-2.0-flash", "finish_reason": "stop"}],
    )


class MessageCreate(MessageBase):
    """Schema for adding a new message to a conversation."""

    pass


class MessageResponse(MessageBase):
    """Schema for returning message records."""

    id: int = Field(..., description="Unique message ID")
    conversation_id: int = Field(
        ..., description="ID of the parent conversation"
    )
    created_at: datetime = Field(
        ..., description="Timestamp when the message was recorded"
    )

    model_config = ConfigDict(from_attributes=True)


class ConversationBase(BaseModel):
    """Shared properties for a chat conversation session."""

    resident_id: int = Field(
        ...,
        description="ID of the resident this conversation belongs to",
        examples=[1],
    )
    user_id: int | None = Field(
        default=None,
        description="Optional ID of staff/caregiver user who initiated the session",
        examples=[2],
    )
    title: str | None = Field(
        default=None,
        max_length=200,
        description="Optional title or summary for the conversation",
        examples=["Morning Check-in"],
    )
    status: str = Field(
        default="active",
        max_length=30,
        description="Session state: 'active', 'archived', or 'closed'",
        examples=["active"],
    )
    extra_metadata: dict[str, Any] | None = Field(
        default=None,
        description="Optional session-level metadata",
        examples=[{"locale": "en_US", "device": "room_tablet"}],
    )


class ConversationCreate(ConversationBase):
    """Schema for creating a new conversation."""

    pass


class ConversationUpdate(BaseModel):
    """Schema for updating an existing conversation session."""

    title: str | None = Field(
        default=None,
        max_length=200,
        description="Updated conversation title",
    )
    status: str | None = Field(
        default=None,
        max_length=30,
        description="Updated status: 'active', 'archived', or 'closed'",
    )
    extra_metadata: dict[str, Any] | None = Field(
        default=None,
        description="Updated metadata dictionary",
    )


class ConversationResponse(ConversationBase):
    """Schema for returning conversation summary data."""

    id: int = Field(..., description="Unique conversation ID")
    created_at: datetime = Field(
        ..., description="Timestamp when the conversation was initiated"
    )
    updated_at: datetime = Field(
        ..., description="Timestamp of the most recent update"
    )

    model_config = ConfigDict(from_attributes=True)


class ConversationDetailResponse(ConversationResponse):
    """Schema for returning a conversation along with its message history."""

    messages: list[MessageResponse] = Field(
        default_factory=list,
        description="Chronologically ordered list of messages in this session",
    )

