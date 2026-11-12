from typing import Any, TypedDict


class ChatGraphState(TypedDict, total=False):
    """Strongly-typed state container for the LangGraph conversational workflow."""

    # Input Identifiers & Request Context
    conversation_id: int
    resident_id: int
    user_id: int | None
    current_message: str
    requested_provider: str | None
    requested_model: str | None

    # Loaded Entity Context
    resident_name: str | None
    resident_room: str | None
    conversation_status: str | None

    # Conversation History & Prompt Context
    conversation_history: list[dict[str, str]]
    system_prompt: str

    # Provider & Model Selection
    selected_provider: str
    selected_model: str

    # Safety & Validation Metadata
    safety_metadata: dict[str, Any]

    # LLM Execution Outputs
    llm_response: str | None
    token_usage: dict[str, int | None]
    latency_ms: float | None
    finish_reason: str | None

    # Persistence Outputs
    persisted_user_message_id: int | None
    persisted_assistant_message_id: int | None

    # Workflow Lifecycle & Error State
    execution_status: str
    error_code: str | None
    error_message: str | None

