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


class ProviderInfoResponse(BaseModel):
    """Schema describing an available LLM provider and its configuration state."""

    provider: str = Field(..., description="Provider identifier ('gemini' or 'openai')")
    default_model: str = Field(..., description="Default model for this provider")
    available_models: list[str] = Field(
        default_factory=list, description="Supported models for this provider"
    )
    is_configured: bool = Field(
        ..., description="Whether the API key for this provider is configured on the server"
    )


class ChatSessionCreateRequest(BaseModel):
    """Schema for creating a new conversational session via REST API."""

    resident_id: int = Field(..., description="ID of the resident")
    title: str | None = Field(
        default=None,
        max_length=200,
        description="Optional conversation title",
    )
    provider: str | None = Field(
        default=None,
        description="Optional LLM provider ('gemini' or 'openai')",
        examples=["gemini"],
    )
    model: str | None = Field(
        default=None,
        description="Optional model identifier",
        examples=["gemini-2.0-flash"],
    )
    extra_metadata: dict[str, Any] | None = Field(
        default=None,
        description="Optional additional session metadata",
    )


class ChatSessionUpdateRequest(BaseModel):
    """Schema for updating conversation title, status, or provider/model configuration."""

    title: str | None = Field(default=None, max_length=200)
    status: str | None = Field(
        default=None,
        max_length=30,
        description="Status ('active', 'archived', 'closed')",
    )
    provider: str | None = Field(
        default=None,
        description="Updated LLM provider ('gemini' or 'openai')",
    )
    model: str | None = Field(
        default=None,
        description="Updated model identifier",
    )
    extra_metadata: dict[str, Any] | None = Field(default=None)


class SendMessageRequest(BaseModel):
    """Schema for sending a user message in a conversation."""

    conversation_id: int = Field(..., description="Target conversation ID")
    message: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="User message text",
        examples=["How can I improve my daily sleep routine?"],
    )
    provider: str | None = Field(
        default=None,
        description="Optional provider override ('gemini' or 'openai')",
    )
    model: str | None = Field(
        default=None,
        description="Optional model override",
    )


class SafetyMetadataResponse(BaseModel):
    """Safety screening results returned with a chat turn."""

    risk_level: str = Field(default="none")
    requires_caregiver_alert: bool = Field(default=False)
    flagged_categories: list[str] = Field(default_factory=list)
    matched_indicators: list[str] = Field(default_factory=list)


class TokenUsageResponse(BaseModel):
    """Token consumption metrics for a chat turn."""

    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


class SendMessageResponse(BaseModel):
    """Complete response returned after processing a conversational turn."""

    conversation_id: int
    resident_id: int
    provider: str
    model: str
    user_message: MessageResponse
    assistant_message: MessageResponse
    safety: SafetyMetadataResponse
    token_usage: TokenUsageResponse
    latency_ms: float | None = None


