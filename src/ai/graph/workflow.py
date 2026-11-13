from langgraph.graph import END, START, StateGraph

from src.ai.graph.edges import (
    route_after_generate_response,
    route_after_load_conversation,
    route_after_select_provider,
    route_after_validate_input,
)
from src.ai.graph.nodes import (
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


def build_chat_workflow():
    """Construct and compile the initial LangGraph conversational state machine."""
    builder = StateGraph(ChatGraphState)

    # Register workflow nodes
    builder.add_node("load_conversation", load_conversation_node)
    builder.add_node(
        "load_conversation_history", load_conversation_history_node
    )
    builder.add_node("validate_input", validate_input_node)
    builder.add_node("retrieve_clinical_rag", retrieve_clinical_rag_node)
    builder.add_node("safety_check", safety_check_node)
    builder.add_node("select_llm_provider", select_llm_provider_node)
    builder.add_node("generate_response", generate_response_node)
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
            "retrieve_clinical_rag": "retrieve_clinical_rag",
            END: END,
        },
    )
    builder.add_edge("retrieve_clinical_rag", "safety_check")
    builder.add_edge("safety_check", "select_llm_provider")
    builder.add_conditional_edges(
        "select_llm_provider",
        route_after_select_provider,
        {
            "generate_response": "generate_response",
            END: END,
        },
    )
    builder.add_conditional_edges(
        "generate_response",
        route_after_generate_response,
        {
            "persist_assistant_message": "persist_assistant_message",
            END: END,
        },
    )
    builder.add_edge("persist_assistant_message", END)

    return builder.compile()


# Singleton compiled workflow instance
chat_workflow = build_chat_workflow()

