"""Conversational AI & LangGraph Chat service wrapper for the Streamlit frontend."""

from typing import Any

from frontend.services.api_client import APIClient


class ChatFrontendService:
    """Service methods for `/api/v1/chat/*` endpoints."""

    def __init__(self, client: APIClient | None = None) -> None:
        self.client = client or APIClient()

    def list_providers(self, token: str) -> list[dict[str, Any]]:
        """Fetch registered LLM providers (Google Gemini, OpenAI GPT-3.5) and their models."""
        return self.client.get("/chat/providers", token=token)

    def create_session(
        self,
        token: str,
        resident_id: int,
        title: str | None = None,
        provider: str | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        """Create a new AI conversation session for a resident."""
        payload: dict[str, Any] = {"resident_id": resident_id}
        if title:
            payload["title"] = title.strip()
        if provider:
            payload["provider"] = provider
        if model:
            payload["model"] = model
        return self.client.post("/chat/sessions", token=token, json=payload)

    def list_sessions(
        self,
        token: str,
        resident_id: int | None = None,
        status_filter: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List accessible chat sessions, optionally filtered by resident_id and status."""
        return self.client.get(
            "/chat/sessions",
            token=token,
            params={
                "resident_id": resident_id,
                "status": status_filter,
                "skip": skip,
                "limit": limit,
            },
        )

    def get_session(self, token: str, session_id: int) -> dict[str, Any]:
        """Retrieve metadata for a specific chat session."""
        return self.client.get(f"/chat/sessions/{session_id}", token=token)

    def update_session(
        self,
        token: str,
        session_id: int,
        title: str | None = None,
        status: str | None = None,
        provider: str | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        """Update session title, status ('active', 'archived', 'closed'), or default LLM provider/model."""
        payload: dict[str, Any] = {}
        if title is not None:
            payload["title"] = title.strip()
        if status is not None:
            payload["status"] = status
        if provider is not None:
            payload["provider"] = provider
        if model is not None:
            payload["model"] = model
        return self.client.patch(
            f"/chat/sessions/{session_id}",
            token=token,
            json=payload,
        )

    def delete_session(self, token: str, session_id: int) -> None:
        """Delete a conversation session and its messages."""
        self.client.delete(f"/chat/sessions/{session_id}", token=token)

    def get_session_history(
        self,
        token: str,
        session_id: int,
    ) -> list[dict[str, Any]]:
        """Fetch chronological message history for a conversation session."""
        return self.client.get(
            f"/chat/sessions/{session_id}/history",
            token=token,
        )

    def send_message(
        self,
        token: str,
        conversation_id: int,
        content: str,
        provider: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Send a user message through the LangGraph workflow and receive the AI response."""
        payload: dict[str, Any] = {
            "conversation_id": conversation_id,
            "message": content,
        }
        if provider:
            payload["provider"] = provider
        if model:
            payload["model"] = model
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        return self.client.post(
            "/chat/message",
            token=token,
            json=payload,
        )

