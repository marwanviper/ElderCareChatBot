import unittest
from collections.abc import Iterator
from datetime import date

from src.ai.exceptions import LLMRateLimitError
from src.ai.providers.base import (
    BaseLLMProvider,
    LLMGenerationRequest,
    LLMGenerationResponse,
)
from src.ai.providers.factory import LLMProviderFactory
from src.ai.services.chat_service import ChatService
from src.crud.chat import (
    create_conversation,
    get_conversation_by_id,
    get_messages_by_conversation,
)
from src.models import Resident, Role, User
from src.schemas.chat import ConversationCreate
from tests.test_base import BaseTestCase


class MockSuccessProvider(BaseLLMProvider):
    """Deterministic mock LLM provider for testing LangGraph execution."""

    def __init__(self, name: str, default_model: str, available_models: list[str]):
        self.provider_name = name
        self.default_model = default_model
        self.available_models = available_models
        self.last_request: LLMGenerationRequest | None = None

    def is_configured(self) -> bool:
        return True

    def generate(self, request: LLMGenerationRequest) -> LLMGenerationResponse:
        self.last_request = request
        model = self.validate_model(request.model)
        user_text = request.messages[-1].content
        return LLMGenerationResponse(
            content=f"[{self.provider_name}:{model}] I heard you say: {user_text}",
            provider=self.provider_name,
            model=model,
            prompt_tokens=25,
            completion_tokens=15,
            total_tokens=40,
            latency_ms=12.5,
            finish_reason="STOP",
        )

    def stream(self, request: LLMGenerationRequest) -> Iterator[str]:
        yield "Mock stream"


class MockFailingProvider(BaseLLMProvider):
    """Mock provider that simulates an upstream rate limit failure."""

    provider_name = "gemini"
    default_model = "gemini-2.0-flash"
    available_models = ["gemini-2.0-flash"]

    def is_configured(self) -> bool:
        return True

    def generate(self, request: LLMGenerationRequest) -> LLMGenerationResponse:
        raise LLMRateLimitError("Simulated rate limit exceeded.")

    def stream(self, request: LLMGenerationRequest) -> Iterator[str]:
        raise LLMRateLimitError("Simulated rate limit exceeded.")


class TestLangGraphWorkflow(BaseTestCase):
    """Integration tests for the LangGraph conversational workflow."""

    def setUp(self):
        super().setUp()
        self.resident = Resident(
            name="Arthur Pendelton",
            date_of_birth=date(1940, 2, 10),
            room_number="108",
        )
        self.user = User(
            name="Caregiver Clara",
            email="clara@eldercare.test",
            password_hash="hashed",
            role=Role.CAREGIVER,
        )
        self.db.add_all([self.resident, self.user])
        self.db.commit()
        self.db.refresh(self.resident)
        self.db.refresh(self.user)

        self.mock_gemini = MockSuccessProvider(
            name="gemini",
            default_model="gemini-2.0-flash",
            available_models=["gemini-2.0-flash", "gemini-1.5-flash"],
        )
        self.mock_openai = MockSuccessProvider(
            name="openai",
            default_model="gpt-3.5-turbo",
            available_models=["gpt-3.5-turbo", "gpt-4o-mini"],
        )
        LLMProviderFactory.register_override("gemini", self.mock_gemini)
        LLMProviderFactory.register_override("openai", self.mock_openai)

    def tearDown(self):
        LLMProviderFactory.clear_overrides()
        super().tearDown()

    def test_graph_executes_and_persists_messages(self):
        """LangGraph should load context, invoke Gemini, and persist both user and assistant messages."""
        conv = create_conversation(
            self.db,
            ConversationCreate(
                resident_id=self.resident.id,
                user_id=self.user.id,
                title="Morning Check",
                extra_metadata={"provider": "gemini", "model": "gemini-2.0-flash"},
            ),
        )

        state = ChatService.process_user_message(
            db=self.db,
            conversation_id=conv.id,
            user_id=self.user.id,
            message_content="Good morning! What is a good stretching exercise?",
        )

        self.assertEqual(state["execution_status"], "completed")
        self.assertEqual(state["selected_provider"], "gemini")
        self.assertEqual(state["selected_model"], "gemini-2.0-flash")
        self.assertIn("[gemini:gemini-2.0-flash]", state["llm_response"])

        messages = get_messages_by_conversation(self.db, conv.id)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].role.value, "user")
        self.assertEqual(messages[1].role.value, "assistant")
        self.assertEqual(messages[1].token_count, 40)

    def test_graph_supports_switching_provider_to_openai_gpt35(self):
        """Switching provider to OpenAI GPT-3.5 mid-conversation should route to OpenAI and update metadata."""
        conv = create_conversation(
            self.db,
            ConversationCreate(
                resident_id=self.resident.id,
                user_id=self.user.id,
                title="Multi-Provider Session",
                extra_metadata={"provider": "gemini", "model": "gemini-2.0-flash"},
            ),
        )

        # Turn 1 with Gemini
        ChatService.process_user_message(
            db=self.db,
            conversation_id=conv.id,
            user_id=self.user.id,
            message_content="Hello Gemini!",
        )

        # Turn 2 switching to OpenAI gpt-3.5-turbo
        state2 = ChatService.process_user_message(
            db=self.db,
            conversation_id=conv.id,
            user_id=self.user.id,
            message_content="Now answer with OpenAI GPT-3.5.",
            provider="openai",
            model="gpt-3.5-turbo",
        )

        self.assertEqual(state2["execution_status"], "completed")
        self.assertEqual(state2["selected_provider"], "openai")
        self.assertEqual(state2["selected_model"], "gpt-3.5-turbo")
        self.assertIn("[openai:gpt-3.5-turbo]", state2["llm_response"])

        # Verify history of 4 messages (2 turns)
        messages = get_messages_by_conversation(self.db, conv.id)
        self.assertEqual(len(messages), 4)

        # Verify OpenAI received previous conversation history
        self.assertEqual(len(self.mock_openai.last_request.messages), 3)

        # Verify conversation default metadata updated to openai
        updated_conv = get_conversation_by_id(self.db, conv.id)
        self.assertEqual(updated_conv.extra_metadata["provider"], "openai")
        self.assertEqual(updated_conv.extra_metadata["model"], "gpt-3.5-turbo")

    def test_graph_llm_failure_does_not_corrupt_history(self):
        """If the LLM provider fails, no orphaned user message should be written to the database."""
        LLMProviderFactory.register_override("gemini", MockFailingProvider())

        conv = create_conversation(
            self.db,
            ConversationCreate(
                resident_id=self.resident.id,
                user_id=self.user.id,
                title="Failure Resilience Test",
            ),
        )

        state = ChatService.process_user_message(
            db=self.db,
            conversation_id=conv.id,
            user_id=self.user.id,
            message_content="Will this message be orphaned if the API fails?",
            provider="gemini",
        )

        self.assertEqual(state["execution_status"], "failed")
        self.assertEqual(state["error_code"], "llm_rate_limit_error")

        # Database history must remain completely empty (0 messages)
        messages = get_messages_by_conversation(self.db, conv.id)
        self.assertEqual(len(messages), 0)


if __name__ == "__main__":
    unittest.main()

