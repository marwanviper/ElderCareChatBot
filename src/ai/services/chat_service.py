from sqlalchemy.orm import Session

from src.ai.graph.state import ChatGraphState
from src.ai.graph.workflow import chat_workflow


class ChatService:
    """Service layer orchestrating conversational turns via the LangGraph workflow."""

    @staticmethod
    def process_user_message(
        db: Session,
        conversation_id: int,
        user_id: int | None,
        message_content: str,
        provider: str | None = None,
        model: str | None = None,
    ) -> ChatGraphState:
        """Execute the full conversational LangGraph pipeline for a single turn."""
        initial_state: ChatGraphState = {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "current_message": message_content,
            "requested_provider": provider,
            "requested_model": model,
            "execution_status": "initialized",
        }

        result_state: ChatGraphState = chat_workflow.invoke(
            initial_state,
            config={"configurable": {"db": db}},
        )
        return result_state

