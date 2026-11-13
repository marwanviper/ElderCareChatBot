"""Unit and integration tests for Clinical Vector Database, Embeddings, and RAG Pipeline."""

import unittest
from datetime import date
from unittest.mock import MagicMock

from src.ai.embeddings.base import BaseEmbeddingProvider
from src.ai.embeddings.factory import EmbeddingProviderFactory
from src.ai.services.chat_service import ChatService
from src.ai.services.rag_service import RAGService
from src.crud.chat import create_conversation
from src.models import (
    CareGoal,
    CareReport,
    ClinicalEmbedding,
    Incident,
    Resident,
    Role,
    User,
)
from src.schemas.chat import ConversationCreate
from tests.test_ai_graph import MockSuccessProvider
from tests.test_base import BaseTestCase


class MockDeterministicEmbeddingProvider(BaseEmbeddingProvider):
    """Mock embedding provider that returns distinct, predictable vectors."""

    provider_name = "mock"
    dimension = 4

    def __init__(self):
        # 4D vector dictionary for predictable cosine similarity testing
        self.vectors = {
            "mobility": [1.0, 0.0, 0.0, 0.0],
            "fall": [0.95, 0.1, 0.0, 0.0],
            "diet": [0.0, 1.0, 0.0, 0.0],
            "sleep": [0.0, 0.0, 1.0, 0.0],
            "default": [0.1, 0.1, 0.1, 0.1],
        }

    def is_configured(self) -> bool:
        return True

    def embed_text(self, text: str) -> list[float]:
        t_low = text.lower()
        if "fall" in t_low:
            return self.vectors["fall"]
        elif "walk" in t_low or "mobility" in t_low:
            return self.vectors["mobility"]
        elif "diet" in t_low or "eat" in t_low or "food" in t_low:
            return self.vectors["diet"]
        elif "sleep" in t_low or "night" in t_low:
            return self.vectors["sleep"]
        return self.vectors["default"]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text(t) for t in texts]


class TestClinicalRAGAndEmbeddings(BaseTestCase):
    """Tests for indexing, semantic retrieval, and LangGraph RAG grounding."""

    def setUp(self):
        super().setUp()
        self.resident1 = Resident(
            name="Arthur Pendelton",
            date_of_birth=date(1940, 2, 10),
            room_number="108",
        )
        self.resident2 = Resident(
            name="Clara Oswald",
            date_of_birth=date(1945, 8, 22),
            room_number="204",
        )
        self.user = User(
            name="Nurse Sarah",
            email="sarah@eldercare.test",
            password_hash="hashed",
            role=Role.CAREGIVER,
        )
        self.db.add_all([self.resident1, self.resident2, self.user])
        self.db.commit()
        self.db.refresh(self.resident1)
        self.db.refresh(self.resident2)
        self.db.refresh(self.user)

        # Register mock embedding provider
        self.mock_embedder = MockDeterministicEmbeddingProvider()
        EmbeddingProviderFactory.register_override("gemini", self.mock_embedder)
        EmbeddingProviderFactory.register_override("openai", self.mock_embedder)

        # Register mock LLM provider
        self.mock_llm = MockSuccessProvider(
            name="gemini",
            default_model="gemini-3.5-flash",
            available_models=["gemini-3.5-flash", "gemini-1.5-flash"],
        )
        from src.ai.providers.factory import LLMProviderFactory
        LLMProviderFactory.register_override("gemini", self.mock_llm)

    def tearDown(self):
        EmbeddingProviderFactory.clear_overrides()
        from src.ai.providers.factory import LLMProviderFactory
        LLMProviderFactory.clear_overrides()
        super().tearDown()

    def test_indexing_care_report_and_incident(self):
        """RAGService should vectorize care reports and incidents into clinical_embeddings."""
        rep = CareReport(
            resident_id=self.resident1.id,
            content="Resident completed 20 minutes of walking exercises today.",
            created_by=self.user.id,
        )
        inc = Incident(
            resident_id=self.resident1.id,
            type="Fall",
            description="Resident slipped near bathroom entrance. Vitals normal.",
        )
        self.db.add_all([rep, inc])
        self.db.commit()

        # Index both records
        RAGService.index_care_report(self.db, rep)
        RAGService.index_incident(self.db, inc)

        embeddings = (
            self.db.query(ClinicalEmbedding)
            .filter(ClinicalEmbedding.resident_id == self.resident1.id)
            .all()
        )
        self.assertEqual(len(embeddings), 2)
        sources = {e.source_type for e in embeddings}
        self.assertIn("care_report", sources)
        self.assertIn("incident", sources)

    def test_semantic_retrieval_respects_resident_boundaries(self):
        """Search query for resident 1 must NEVER retrieve clinical records from resident 2."""
        goal1 = CareGoal(
            resident_id=self.resident1.id,
            goal="Walk 300 meters daily in courtyard.",
            status="active",
        )
        goal2 = CareGoal(
            resident_id=self.resident2.id,
            goal="Walk 100 meters with physical therapist.",
            status="active",
        )
        self.db.add_all([goal1, goal2])
        self.db.commit()

        RAGService.index_care_goal(self.db, goal1)
        RAGService.index_care_goal(self.db, goal2)

        # Query relevant context for resident 1
        results = RAGService.search_relevant_context(
            db=self.db,
            resident_id=self.resident1.id,
            query_text="Tell me about walking mobility goals",
            top_k=5,
            threshold=0.5,
        )

        self.assertGreater(len(results), 0)
        self.assertIn("Arthur Pendelton", results[0])
        # Ensure resident 2 record is never leaked
        for r in results:
            self.assertNotIn("Clara Oswald", r)

    def test_langgraph_workflow_executes_rag_node_and_injects_prompt(self):
        """LangGraph should execute retrieve_clinical_rag_node and ground system prompt in retrieved facts."""
        rep = CareReport(
            resident_id=self.resident1.id,
            content="Resident has mild knee pain after afternoon walks.",
            created_by=self.user.id,
        )
        self.db.add(rep)
        self.db.commit()
        RAGService.index_care_report(self.db, rep)

        conv = create_conversation(
            self.db,
            ConversationCreate(
                resident_id=self.resident1.id,
                user_id=self.user.id,
                title="RAG Grounding Test",
                extra_metadata={"provider": "gemini", "model": "gemini-3.5-flash"},
            ),
        )

        state = ChatService.process_user_message(
            db=self.db,
            conversation_id=conv.id,
            user_id=self.user.id,
            message_content="How were Arthur's afternoon walks?",
            provider="gemini",
        )

        self.assertEqual(state["execution_status"], "completed")
        self.assertIn("retrieved_context", state)
        self.assertGreater(len(state["retrieved_context"]), 0)
        # Verify that the LLM system prompt contained the retrieved clinical note
        self.assertIn("mild knee pain", state["system_prompt"])
        self.assertIn("RELEVANT CLINICAL RECORDS & RESIDENT HISTORY", state["system_prompt"])


if __name__ == "__main__":
    unittest.main()
