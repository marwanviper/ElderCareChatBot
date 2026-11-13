from typing import Any
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from src.ai.graph.edges import (
    route_after_generate_response,
    route_after_load_conversation,
    route_after_select_provider,
    route_after_validate_input,
)
from src.ai.graph.nodes import (
    execute_clinical_tool_node,
    generate_response_node,
    load_conversation_history_node,
    load_conversation_node,
    persist_assistant_message_node,
    retrieve_clinical_rag_node,
    safety_check_node,
    select_llm_provider_node,
    validate_input_node,
)
from src.ai.graph.state import ChatGraphState


# Singleton checkpointer for session state preservation
shared_checkpointer = MemorySaver()


def reset_workflow_checkpointer() -> None:
    """Clear in-memory checkpoints between test suites or session resets."""
    if hasattr(shared_checkpointer, "storage") and isinstance(shared_checkpointer.storage, dict):
        shared_checkpointer.storage.clear()
    if hasattr(shared_checkpointer, "writes") and isinstance(shared_checkpointer.writes, dict):
        shared_checkpointer.writes.clear()


def build_chat_workflow(checkpointer: Any = shared_checkpointer):
    """Construct and compile the LangGraph conversational state machine with checkpoint persistence."""
    builder = StateGraph(ChatGraphState)

    # Register workflow nodes
    builder.add_node("load_conversation", load_conversation_node)
    builder.add_node(
        "load_conversation_history", load_conversation_history_node
    )
    builder.add_node("validate_input", validate_input_node)
    builder.add_node("safety_check", safety_check_node)
    builder.add_node("select_llm_provider", select_llm_provider_node)
    builder.add_node("generate_response", generate_response_node)
    builder.add_node("execute_clinical_tool", execute_clinical_tool_node)
    builder.add_node(
        "persist_assistant_message", persist_assistant_message_node
    )

    # Wire edges and conditional failure gates
    builder.add_edge(START, "load_conversation")
    builder.add_conditional_edges(
        "load_conversation",
        route_after_load_conversation,
        {
            "load_conversation_history": "load_conversation_history",
            END: END,
        },
    )
    builder.add_edge("load_conversation_history", "validate_input")
    builder.add_conditional_edges(
        "validate_input",
        route_after_validate_input,
        {
            "safety_check": "safety_check",
            END: END,
        },
    )
    builder.add_edge("safety_check", "select_llm_provider")
    builder.add_conditional_edges(
        "select_llm_provider",
        route_after_select_provider,
        {
            "generate_response": "generate_response",
            END: END,
        },
    )

    # ReAct Reactive Router:
    # If the LLM agent determines it needs clinical records, route to tool execution.
    # Otherwise, proceed directly to persistence.
    builder.add_conditional_edges(
        "generate_response",
        route_after_generate_response,
        {
            "execute_clinical_tool": "execute_clinical_tool",
            "persist_assistant_message": "persist_assistant_message",
            END: END,
        },
    )
    # Reactive loop back to agent reasoning after tool execution
    builder.add_edge("execute_clinical_tool", "generate_response")

    builder.add_edge("persist_assistant_message", END)

    if checkpointer is not None:
        return builder.compile(checkpointer=checkpointer)
    return builder.compile()


# Singleton compiled workflow instance
chat_workflow = build_chat_workflow()

