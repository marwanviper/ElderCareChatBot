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
) -> Literal["safety_check", "__end__"]:
    """Route to safety screening if input is valid, otherwise terminate."""
    if state.get("execution_status") == "failed":
        return END
    return "safety_check"


def route_after_select_provider(
    state: ChatGraphState,
) -> Literal["generate_response", "__end__"]:
    """Route to LLM generation if provider and model are ready, otherwise terminate."""
    if state.get("execution_status") == "failed":
        return END
    return "generate_response"


def route_after_generate_response(
    state: ChatGraphState,
) -> Literal["execute_clinical_tool", "persist_assistant_message", "__end__"]:
    """ReAct router: Dispatch to clinical tool if factual data is needed, else persist response."""
    if state.get("execution_status") == "failed":
        return END

    if state.get("requires_clinical_data"):
        return "execute_clinical_tool"

    return "persist_assistant_message"

