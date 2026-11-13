from typing import Any
from langchain_core.runnables import RunnableConfig
from sqlalchemy.orm import Session

from src.ai.exceptions import AIError
from src.ai.graph.state import ChatGraphState
from src.ai.prompts.elderly_care import build_elderly_care_system_prompt
from src.ai.providers.base import ChatMessageInput, LLMGenerationRequest
from src.ai.providers.factory import LLMProviderFactory
from src.ai.safety.checker import SafetyChecker
from src.ai.services.rag_service import RAGService
from src.core.config import settings
from src.core.logging import logger
from src.crud.chat import (
    create_message,
    get_conversation_by_id,
    get_messages_by_conversation,
    update_conversation,
)
from src.crud.resident import get_resident_by_id
from src.models.message import MessageRole
from src.schemas.chat import ConversationUpdate, MessageCreate


# Clinical, medical, and resident inquiry keywords for Intent-Gated RAG
CLINICAL_INTENT_KEYWORDS: set[str] = {
    # English keywords
    "med", "medication", "pill", "pills", "dose", "dosage", "drug", "prescription",
    "pain", "hurt", "hurts", "ache", "sore", "headache", "chest", "dizzy", "dizziness",
    "fall", "fell", "fallen", "slip", "injury", "wound", "bruise", "bleeding",
    "sleep", "asleep", "insomnia", "tired", "rest", "fatigue", "night",
    "eat", "eating", "food", "appetite", "breakfast", "lunch", "dinner", "meal",
    "incident", "accident", "emergency", "urgent",
    "report", "note", "notes", "observation", "goal", "goals", "plan", "care plan",
    "doctor", "nurse", "physician", "hospital", "clinic", "appointment",
    "blood", "pressure", "hypertension", "sugar", "glucose", "diabetes",
    "fever", "temperature", "vital", "vitals", "pulse", "heart",
    "walk", "walking", "walks", "mobility", "wheelchair", "cane", "exercise",
    "status", "condition", "history", "record", "records", "diagnosis",
    "allergy", "allergic", "reaction", "symptom", "symptoms", "care",
    # Arabic keywords
    "دواء", "ادوية", "أدوية", "علاج", "حبوب", "جرعة", "روشتة",
    "الم", "ألم", "وجع", "صداع", "صدر", "دوخة", "دوار",
    "سقوط", "وقع", "وقوع", "اصابة", "إصابة", "جرح", "كدمة", "نزيف",
    "نوم", "نايم", "أرق", "تعب", "إرهاق",
    "أكل", "اكل", "طعام", "شهية", "وجبة", "فطار", "غداء", "عشاء",
    "حادث", "طوارئ", "طارئ",
    "تقرير", "ملاحظة", "هدف", "اهداف", "أهداف", "خطة", "خطة رعاية",
    "دكتور", "طبيب", "ممرض", "ممرضة", "مستشفى", "عيادة", "موعد",
    "ضغط", "سكر", "حرارة", "نبض", "قلب", "فحص",
    "مشي", "حركة", "كرسي", "عكاز", "تمارين",
    "حالة", "صحة", "تاريخ", "سجل", "سجلات", "تشخيص",
    "حساسية", "عرض", "اعراض", "أعراض",
}


def _should_retrieve_clinical_rag(message: str) -> bool:
    """Determine whether a message requires external vector embedding and clinical RAG retrieval."""
    if not message or not message.strip():
        return False

    cleaned = message.strip().lower()
    words = cleaned.split()

    common_chitchat = {
        "hi", "hello", "hey", "howdy", "good morning", "good afternoon",
        "good evening", "good night", "thanks", "thank you", "thx",
        "ok", "okay", "k", "yes", "no", "yep", "nope", "bye", "goodbye",
        "who are you", "what can you do", "help",
        "أهلا", "أهلاً", "مرحبا", "مرحباً", "صباح الخير", "مساء الخير",
        "شكرا", "شكراً", "تمام", "ماشي", "نعم", "لا", "باي", "مع السلامة",
        "مين انت", "إنت مين",
    }
    if cleaned in common_chitchat:
        return False

    # Check for clinical intent keywords
    for kw in CLINICAL_INTENT_KEYWORDS:
        if kw in cleaned:
            return True

    # Check for resident inquiry phrases
    inquiry_patterns = [
        "how is", "how are", "what happened", "did he", "did she",
        "tell me about", "update on", "any updates", "can you check",
        "اخبار", "أخبار", "عامل ايه", "عاملة ايه", "طمني", "طمئني", "ايه وضعه", "إيه وضعه"
    ]
    for pattern in inquiry_patterns:
        if pattern in cleaned:
            return True

    return len(words) > 5


def _get_db_from_config(config: RunnableConfig) -> Session:
    """Extract the active SQLAlchemy Session from LangGraph RunnableConfig."""
    configurable = config.get("configurable", {}) if config else {}
    db = configurable.get("db")
    if db is None:
        raise RuntimeError(
            "Database session missing from LangGraph RunnableConfig['configurable']['db']"
        )
    return db


def load_conversation_node(
    state: ChatGraphState, config: RunnableConfig
) -> dict[str, Any]:
    """Node 1: Load and validate the target Conversation and Resident records."""
    conversation_id = state.get("conversation_id")
    if not conversation_id:
        return {
            "execution_status": "failed",
            "error_code": "invalid_conversation",
            "error_message": "Conversation ID is required.",
        }

    # Fast-path cache: If resident & conversation metadata are already in state from checkpoint
    cached_resident_id = state.get("resident_id")
    cached_resident_name = state.get("resident_name")
    if cached_resident_id and cached_resident_name:
        conv_status = state.get("conversation_status", "active")
        if conv_status == "closed":
            return {
                "execution_status": "failed",
                "error_code": "conversation_closed",
                "error_message": "Cannot send messages to a closed conversation.",
            }
        return {
            "selected_provider": state.get("requested_provider")
            or state.get("selected_provider")
            or settings.DEFAULT_LLM_PROVIDER,
            "selected_model": state.get("requested_model")
            or state.get("selected_model")
            or "",
            "execution_status": "conversation_loaded",
        }

    db = _get_db_from_config(config)
    conv = get_conversation_by_id(db, conversation_id)
    if not conv:
        return {
            "execution_status": "failed",
            "error_code": "conversation_not_found",
            "error_message": f"Conversation with ID {conversation_id} not found.",
        }

    if conv.status == "closed":
        return {
            "execution_status": "failed",
            "error_code": "conversation_closed",
            "error_message": "Cannot send messages to a closed conversation.",
        }

    resident = get_resident_by_id(db, conv.resident_id)
    if not resident:
        return {
            "execution_status": "failed",
            "error_code": "resident_not_found",
            "error_message": f"Resident with ID {conv.resident_id} not found.",
        }

    meta = conv.extra_metadata or {}
    stored_provider = meta.get("provider")
    stored_model = meta.get("model")

    return {
        "resident_id": conv.resident_id,
        "resident_name": resident.name,
        "resident_room": resident.room_number,
        "conversation_status": conv.status,
        "selected_provider": state.get("requested_provider")
        or stored_provider
        or settings.DEFAULT_LLM_PROVIDER,
        "selected_model": state.get("requested_model") or stored_model or "",
        "execution_status": "conversation_loaded",
    }


def load_conversation_history_node(
    state: ChatGraphState, config: RunnableConfig
) -> dict[str, Any]:
    """Node 2: Load chronological conversation history bounded by context window."""
    # Fast-path cache: If history is already maintained in state, bypass DB query
    cached_history = state.get("conversation_history")
    if cached_history is not None and len(cached_history) > 0:
        max_history = max(1, settings.CHAT_MAX_HISTORY_MESSAGES)
        return {
            "conversation_history": cached_history[-max_history:],
            "execution_status": "history_loaded",
        }

    db = _get_db_from_config(config)
    conversation_id = state["conversation_id"]

    all_messages = get_messages_by_conversation(
        db, conversation_id=conversation_id, skip=0, limit=200
    )
    max_history = max(1, settings.CHAT_MAX_HISTORY_MESSAGES)
    recent_messages = all_messages[-max_history:] if all_messages else []

    history: list[dict[str, str]] = [
        {"role": str(m.role.value if hasattr(m.role, "value") else m.role), "content": m.content}
        for m in recent_messages
    ]

    return {
        "conversation_history": history,
        "execution_status": "history_loaded",
    }


def validate_input_node(state: ChatGraphState) -> dict[str, Any]:
    """Node 3: Validate and sanitize the incoming user message."""
    raw_msg = state.get("current_message", "")
    if not isinstance(raw_msg, str) or not raw_msg.strip():
        return {
            "execution_status": "failed",
            "error_code": "empty_message",
            "error_message": "Message content cannot be empty.",
        }

    cleaned = raw_msg.strip()
    if len(cleaned) > 4000:
        return {
            "execution_status": "failed",
            "error_code": "message_too_long",
            "error_message": "Message exceeds maximum length of 4000 characters.",
        }

    return {
        "current_message": cleaned,
        "execution_status": "input_validated",
    }


def execute_clinical_tool_node(
    state: ChatGraphState, config: RunnableConfig
) -> dict[str, Any]:
    """ReAct Tool Node: Executes clinical vector retrieval and enriches the system prompt."""
    resident_id = state.get("resident_id")
    query_text = state.get("tool_query") or state.get("current_message", "")

    db = _get_db_from_config(config)
    context_chunks = []
    if resident_id and query_text:
        try:
            context_chunks = RAGService.search_relevant_context(
                db=db,
                resident_id=resident_id,
                query_text=query_text,
                top_k=4,
                threshold=0.25,
                provider_name=state.get("selected_provider"),
            )
        except Exception as exc:
            logger.warning("ReAct clinical tool execution skipped due to non-fatal error: %s", exc)
            context_chunks = []

    # Rebuild system prompt incorporating the freshly retrieved clinical facts
    safety_meta = state.get("safety_metadata") or {}
    updated_system_prompt = build_elderly_care_system_prompt(
        resident_name=state.get("resident_name"),
        room_number=state.get("resident_room"),
        safety_directive=safety_meta.get("safety_directive"),
        clinical_context=context_chunks,
    )

    logger.info(
        "ReAct clinical tool executed: retrieved %d clinical chunks for resident %s",
        len(context_chunks),
        resident_id,
    )

    return {
        "retrieved_context": context_chunks,
        "system_prompt": updated_system_prompt,
        "requires_clinical_data": False,
        "tool_execution_count": (state.get("tool_execution_count") or 0) + 1,
        "execution_status": "tool_executed",
    }


# Backwards compatibility alias
retrieve_clinical_rag_node = execute_clinical_tool_node


def safety_check_node(state: ChatGraphState) -> dict[str, Any]:
    """Node 4: Screen user message for clinical or emergency safety concerns and build prompt."""
    user_message = state["current_message"]
    safety_result = SafetyChecker.evaluate(user_message)
    retrieved_context = state.get("retrieved_context", [])

    system_prompt = build_elderly_care_system_prompt(
        resident_name=state.get("resident_name"),
        room_number=state.get("resident_room"),
        safety_directive=safety_result.safety_directive,
        clinical_context=retrieved_context,
    )

    if safety_result.requires_caregiver_alert:
        logger.warning(
            "High-priority safety alert triggered in conversation %s for resident %s (categories=%s)",
            state.get("conversation_id"),
            state.get("resident_id"),
            safety_result.flagged_categories,
        )

    return {
        "safety_metadata": safety_result.to_dict(),
        "system_prompt": system_prompt,
        "execution_status": "safety_checked",
    }


def select_llm_provider_node(state: ChatGraphState) -> dict[str, Any]:
    """Node 5: Resolve, validate, and verify readiness of the requested LLM provider and model."""
    provider_name = state.get("selected_provider") or settings.DEFAULT_LLM_PROVIDER
    requested_model = state.get("selected_model") or None

    try:
        provider = LLMProviderFactory.get_provider(provider_name)
        provider.ensure_configured()
        resolved_model = provider.validate_model(requested_model)
    except AIError as exc:
        return {
            "execution_status": "failed",
            "error_code": exc.error_code,
            "error_message": exc.message,
        }
    except Exception as exc:
        logger.error("Unexpected error selecting LLM provider: %s", type(exc).__name__)
        return {
            "execution_status": "failed",
            "error_code": "provider_selection_error",
            "error_message": "Failed to initialize the selected LLM provider.",
        }

    return {
        "selected_provider": provider.provider_name,
        "selected_model": resolved_model,
        "execution_status": "provider_selected",
    }


def generate_response_node(state: ChatGraphState) -> dict[str, Any]:
    """Node 6 (ReAct Agent Node): Reason about the turn, invoke clinical tool if needed, or generate response."""
    current_message = state["current_message"]
    tool_count = state.get("tool_execution_count") or 0
    retrieved_context = state.get("retrieved_context") or []

    # ReAct Decision: If clinical data is required and tool has not run yet in this turn, route to tool
    if tool_count == 0 and not retrieved_context and _should_retrieve_clinical_rag(current_message):
        logger.info("ReAct Agent: Turn requires clinical records. Routing to execute_clinical_tool...")
        return {
            "requires_clinical_data": True,
            "tool_query": current_message,
            "execution_status": "tool_requested",
        }

    provider_name = state["selected_provider"]
    model_name = state["selected_model"]
    system_prompt = state["system_prompt"]
    history_dicts = state.get("conversation_history", [])

    messages_input: list[ChatMessageInput] = [
        ChatMessageInput(role=item["role"], content=item["content"])
        for item in history_dicts
    ]
    messages_input.append(
        ChatMessageInput(role="user", content=current_message)
    )

    gen_request = LLMGenerationRequest(
        messages=messages_input,
        system_prompt=system_prompt,
        model=model_name,
        temperature=settings.CHAT_DEFAULT_TEMPERATURE,
        max_tokens=settings.CHAT_DEFAULT_MAX_TOKENS,
    )

    try:
        provider = LLMProviderFactory.get_provider(provider_name)
        gen_response = provider.generate(gen_request)
    except AIError as exc:
        return {
            "execution_status": "failed",
            "error_code": exc.error_code,
            "error_message": exc.message,
        }
    except Exception as exc:
        logger.error("Unhandled error during LLM generation: %s", type(exc).__name__)
        return {
            "execution_status": "failed",
            "error_code": "llm_provider_error",
            "error_message": "An unexpected error occurred while generating the AI response.",
        }

    return {
        "llm_response": gen_response.content,
        "selected_provider": gen_response.provider,
        "selected_model": gen_response.model,
        "token_usage": {
            "prompt_tokens": gen_response.prompt_tokens,
            "completion_tokens": gen_response.completion_tokens,
            "total_tokens": gen_response.total_tokens,
        },
        "latency_ms": gen_response.latency_ms,
        "finish_reason": gen_response.finish_reason,
        "requires_clinical_data": False,
        "execution_status": "response_generated",
    }


def persist_assistant_message_node(
    state: ChatGraphState, config: RunnableConfig
) -> dict[str, Any]:
    """Node 7: Persist both the user message and assistant response atomically after LLM success."""
    db = _get_db_from_config(config)
    conversation_id = state["conversation_id"]
    user_content = state["current_message"]
    assistant_content = state["llm_response"]
    token_usage = state.get("token_usage") or {}
    total_tokens = token_usage.get("total_tokens")
    safety_metadata = state.get("safety_metadata") or {}

    try:
        user_msg = create_message(
            db,
            conversation_id=conversation_id,
            msg_data=MessageCreate(
                role=MessageRole.USER,
                content=user_content,
                token_count=token_usage.get("prompt_tokens"),
                extra_metadata={"safety": safety_metadata} if safety_metadata else None,
            ),
        )

        assistant_meta = {
            "provider": state["selected_provider"],
            "model": state["selected_model"],
            "latency_ms": state.get("latency_ms"),
            "finish_reason": state.get("finish_reason"),
            "token_usage": token_usage,
            "safety": safety_metadata,
        }

        assistant_msg = create_message(
            db,
            conversation_id=conversation_id,
            msg_data=MessageCreate(
                role=MessageRole.ASSISTANT,
                content=assistant_content or "",
                token_count=total_tokens,
                extra_metadata=assistant_meta,
            ),
        )

        # Update conversation metadata with active provider & model
        conv = get_conversation_by_id(db, conversation_id)
        if conv:
            updated_meta = dict(conv.extra_metadata or {})
            updated_meta["provider"] = state["selected_provider"]
            updated_meta["model"] = state["selected_model"]
            update_conversation(
                db,
                conversation_id=conversation_id,
                conv_data=ConversationUpdate(extra_metadata=updated_meta),
            )

        # Update in-memory cached history for fast subsequent turns
        current_history = list(state.get("conversation_history") or [])
        current_history.append({"role": "user", "content": user_content})
        current_history.append({"role": "assistant", "content": assistant_content or ""})
        max_history = max(1, settings.CHAT_MAX_HISTORY_MESSAGES)
        updated_history = current_history[-max_history:]

        return {
            "persisted_user_message_id": user_msg.id,
            "persisted_assistant_message_id": assistant_msg.id,
            "conversation_history": updated_history,
            "execution_status": "completed",
        }
    except Exception as exc:
        db.rollback()
        logger.error("Database failure persisting chat messages: %s", type(exc).__name__)
        return {
            "execution_status": "failed",
            "error_code": "database_persistence_error",
            "error_message": "Failed to persist conversation messages.",
        }

