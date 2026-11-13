from typing import Literal
from langgraph.graph import END

from src.ai.graph.state import ChatGraphState


def route_after_load_conversation(
    state: ChatGraphState,
) -> Literal["load_conversation_history", "__end__"]:
    """Route to history loading if conversation is valid, otherwise terminate."""
    if state.get("execution_status") == "failed":
        return END
    return "load_conversation_history"


def route_after_validate_input(
    state: ChatGraphState,
) -> Literal["retrieve_clinical_rag", "__end__"]:
    """Route to clinical RAG retrieval if input is valid, otherwise terminate."""
    if state.get("execution_status") == "failed":
        return END
    return "retrieve_clinical_rag"


def route_after_select_provider(
    state: ChatGraphState,
) -> Literal["generate_response", "__end__"]:
    """Route to LLM generation if provider and model are ready, otherwise terminate."""
    if state.get("execution_status") == "failed":
        return END
    return "generate_response"


def route_after_generate_response(
    state: ChatGraphState,
) -> Literal["persist_assistant_message", "__end__"]:
    """Route to database persistence only if LLM generation succeeded."""
    if state.get("execution_status") == "failed":
        return END
    return "persist_assistant_message"

