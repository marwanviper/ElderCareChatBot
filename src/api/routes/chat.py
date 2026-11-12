from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.ai.exceptions import AIError
from src.ai.providers.factory import LLMProviderFactory
from src.ai.services.chat_service import ChatService
from src.api.deps import (
    get_current_user,
    get_db,
    verify_resident_access,
)
from src.core.logging import logger
from src.crud.chat import (
    create_conversation,
    delete_conversation,
    get_conversation_by_id,
    get_conversations_by_resident,
    get_messages_by_conversation,
    update_conversation,
)
from src.crud.user_resident_permission import get_permissions_by_user
from src.models.conversation import Conversation
from src.models.message import Message
from src.models.user import Role, User
from src.schemas.chat import (
    ChatSessionCreateRequest,
    ChatSessionUpdateRequest,
    ConversationCreate,
    ConversationResponse,
    ConversationUpdate,
    MessageResponse,
    ProviderInfoResponse,
    SafetyMetadataResponse,
    SendMessageRequest,
    SendMessageResponse,
    TokenUsageResponse,
)

router = APIRouter(prefix="/chat", tags=["AI Chat & Conversations"])


@router.get(
    "/providers",
    response_model=list[ProviderInfoResponse],
    summary="List available LLM providers and models",
)
def list_providers(
    _current_user: User = Depends(get_current_user),
) -> list[dict]:
    """Return all supported LLM providers, their models, and server configuration readiness."""
    return LLMProviderFactory.list_providers_info()


@router.post(
    "/sessions",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new chat conversation session",
)
def create_chat_session(
    session_data: ChatSessionCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Conversation:
    """Create a new conversation associated with an accessible resident."""
    verify_resident_access(
        resident_id=session_data.resident_id,
        current_user=current_user,
        db=db,
    )

    try:
        provider = LLMProviderFactory.get_provider(session_data.provider)
        resolved_model = provider.validate_model(session_data.model)
    except AIError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.message,
        ) from exc

    meta = dict(session_data.extra_metadata or {})
    meta["provider"] = provider.provider_name
    meta["model"] = resolved_model

    conv = create_conversation(
        db,
        conv_data=ConversationCreate(
            resident_id=session_data.resident_id,
            user_id=current_user.id,
            title=session_data.title or f"Chat ({provider.provider_name})",
            status="active",
            extra_metadata=meta,
        ),
    )
    logger.info(
        "Created chat session %s for resident %s by user %s (provider=%s, model=%s)",
        conv.id,
        conv.resident_id,
        current_user.id,
        provider.provider_name,
        resolved_model,
    )
    return conv


@router.get(
    "/sessions",
    response_model=list[ConversationResponse],
    summary="List accessible chat conversations",
)
def list_chat_sessions(
    resident_id: int | None = Query(default=None, description="Filter by resident ID"),
    status_filter: str | None = Query(
        default=None, alias="status", description="Filter by status ('active', 'archived', 'closed')"
    ),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Conversation]:
    """List conversations accessible to the current user, with optional resident and status filters."""
    if resident_id is not None:
        verify_resident_access(
            resident_id=resident_id, current_user=current_user, db=db
        )
        return get_conversations_by_resident(
            db,
            resident_id=resident_id,
            skip=skip,
            limit=limit,
            status=status_filter,
        )

    query = db.query(Conversation)
    if current_user.role != Role.ADMIN:
        permissions = get_permissions_by_user(db, current_user.id)
        allowed_resident_ids = [p.resident_id for p in permissions]
        if not allowed_resident_ids:
            return []
        query = query.filter(Conversation.resident_id.in_(allowed_resident_ids))

    if status_filter is not None:
        query = query.filter(Conversation.status == status_filter)

    return (
        query.order_by(Conversation.updated_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get(
    "/sessions/{session_id}",
    response_model=ConversationResponse,
    summary="Get chat session details",
)
def get_chat_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Conversation:
    """Retrieve a conversation session by ID after verifying resident access."""
    conv = get_conversation_by_id(db, session_id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation with ID {session_id} not found",
        )
    verify_resident_access(
        resident_id=conv.resident_id, current_user=current_user, db=db
    )
    return conv


@router.patch(
    "/sessions/{session_id}",
    response_model=ConversationResponse,
    summary="Update chat session configuration or status",
)
def update_chat_session(
    session_id: int,
    update_data: ChatSessionUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Conversation:
    """Update title, status, or selected LLM provider/model for a conversation."""
    conv = get_conversation_by_id(db, session_id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation with ID {session_id} not found",
        )
    verify_resident_access(
        resident_id=conv.resident_id, current_user=current_user, db=db
    )

    meta = dict(conv.extra_metadata or {})
    if update_data.extra_metadata:
        meta.update(update_data.extra_metadata)

    if update_data.provider is not None or update_data.model is not None:
        target_provider_name = update_data.provider or meta.get("provider")
        try:
            provider = LLMProviderFactory.get_provider(target_provider_name)
            resolved_model = provider.validate_model(update_data.model)
        except AIError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=exc.message,
            ) from exc
        meta["provider"] = provider.provider_name
        meta["model"] = resolved_model

    updated = update_conversation(
        db,
        conversation_id=session_id,
        conv_data=ConversationUpdate(
            title=update_data.title,
            status=update_data.status,
            extra_metadata=meta,
        ),
    )
    return updated


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a chat conversation session",
)
def delete_chat_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a conversation and all its messages."""
    conv = get_conversation_by_id(db, session_id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation with ID {session_id} not found",
        )
    verify_resident_access(
        resident_id=conv.resident_id, current_user=current_user, db=db
    )
    delete_conversation(db, session_id)
    logger.info("Deleted conversation %s by user %s", session_id, current_user.id)


@router.get(
    "/sessions/{session_id}/history",
    response_model=list[MessageResponse],
    summary="Get chronological message history for a conversation",
)
def get_chat_history(
    session_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Message]:
    """Retrieve messages in chronological order for a specific conversation."""
    conv = get_conversation_by_id(db, session_id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation with ID {session_id} not found",
        )
    verify_resident_access(
        resident_id=conv.resident_id, current_user=current_user, db=db
    )
    return get_messages_by_conversation(
        db, conversation_id=session_id, skip=skip, limit=limit
    )


@router.post(
    "/message",
    response_model=SendMessageResponse,
    summary="Send a message and generate an AI response via LangGraph",
)
def send_chat_message(
    payload: SendMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SendMessageResponse:
    """Authenticate user, verify resident access, execute the LangGraph workflow, and return the turn result."""
    conv = get_conversation_by_id(db, payload.conversation_id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation with ID {payload.conversation_id} not found",
        )

    verify_resident_access(
        resident_id=conv.resident_id,
        current_user=current_user,
        db=db,
    )

    result_state = ChatService.process_user_message(
        db=db,
        conversation_id=payload.conversation_id,
        user_id=current_user.id,
        message_content=payload.message,
        provider=payload.provider,
        model=payload.model,
    )

    if result_state.get("execution_status") != "completed":
        err_code = result_state.get("error_code", "ai_error")
        err_msg = result_state.get("error_message", "Failed to process chat message.")

        status_map = {
            "empty_message": status.HTTP_400_BAD_REQUEST,
            "message_too_long": status.HTTP_400_BAD_REQUEST,
            "conversation_closed": status.HTTP_400_BAD_REQUEST,
            "llm_model_not_supported": status.HTTP_400_BAD_REQUEST,
            "conversation_not_found": status.HTTP_404_NOT_FOUND,
            "resident_not_found": status.HTTP_404_NOT_FOUND,
            "llm_rate_limit_error": status.HTTP_429_TOO_MANY_REQUESTS,
            "llm_configuration_error": status.HTTP_503_SERVICE_UNAVAILABLE,
            "llm_provider_error": status.HTTP_502_BAD_GATEWAY,
        }
        http_status = status_map.get(
            err_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        raise HTTPException(status_code=http_status, detail=err_msg)

    user_msg_id = result_state["persisted_user_message_id"]
    assistant_msg_id = result_state["persisted_assistant_message_id"]

    user_msg = db.query(Message).filter(Message.id == user_msg_id).first()
    assistant_msg = (
        db.query(Message).filter(Message.id == assistant_msg_id).first()
    )

    safety_dict = result_state.get("safety_metadata") or {}
    token_dict = result_state.get("token_usage") or {}

    return SendMessageResponse(
        conversation_id=conv.id,
        resident_id=conv.resident_id,
        provider=result_state["selected_provider"],
        model=result_state["selected_model"],
        user_message=MessageResponse.model_validate(user_msg),
        assistant_message=MessageResponse.model_validate(assistant_msg),
        safety=SafetyMetadataResponse(**safety_dict),
        token_usage=TokenUsageResponse(**token_dict),
        latency_ms=result_state.get("latency_ms"),
    )

