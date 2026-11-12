import unittest
from datetime import date

from src.ai.providers.factory import LLMProviderFactory
from src.crud.resident import create_resident
from src.crud.user_resident_permission import create_user_resident_permission
from src.schemas.resident import ResidentCreate
from src.schemas.user_resident_permission import UserResidentPermissionCreate
from tests.test_ai_graph import MockSuccessProvider
from tests.test_api_base import ApiTestCase


class TestApiChat(ApiTestCase):
    """Integration tests for /api/v1/chat endpoints, RBAC, and provider switching."""

    def setUp(self):
        super().setUp()
        self.admin = self.create_test_user(
            name="Admin User", email="admin@eldercare.test", role="admin"
        )
        self.cg_assigned = self.create_test_user(
            name="Assigned CG", email="cg1@eldercare.test", role="caregiver"
        )
        self.cg_unassigned = self.create_test_user(
            name="Unassigned CG", email="cg2@eldercare.test", role="caregiver"
        )

        self.admin_headers = self.get_auth_headers(self.admin)
        self.cg1_headers = self.get_auth_headers(self.cg_assigned)
        self.cg2_headers = self.get_auth_headers(self.cg_unassigned)

        self.resident1 = create_resident(
            self.db,
            ResidentCreate(
                name="Resident One",
                date_of_birth=date(1940, 1, 1),
                room_number="101",
            ),
        )
        self.resident2 = create_resident(
            self.db,
            ResidentCreate(
                name="Resident Two",
                date_of_birth=date(1942, 6, 15),
                room_number="102",
            ),
        )

        # Grant cg_assigned access ONLY to resident1
        create_user_resident_permission(
            self.db,
            UserResidentPermissionCreate(
                user_id=self.cg_assigned.id, resident_id=self.resident1.id
            ),
        )

        # Register mock providers
        LLMProviderFactory.register_override(
            "gemini",
            MockSuccessProvider(
                name="gemini",
                default_model="gemini-2.0-flash",
                available_models=["gemini-2.0-flash", "gemini-1.5-flash"],
            ),
        )
        LLMProviderFactory.register_override(
            "openai",
            MockSuccessProvider(
                name="openai",
                default_model="gpt-3.5-turbo",
                available_models=["gpt-3.5-turbo", "gpt-4o-mini"],
            ),
        )

    def tearDown(self):
        LLMProviderFactory.clear_overrides()
        super().tearDown()

    def test_list_providers_endpoint(self):
        """GET /api/v1/chat/providers should return both gemini and openai."""
        resp = self.client.get(
            "/api/v1/chat/providers", headers=self.cg1_headers
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        providers = {item["provider"]: item for item in data}
        self.assertIn("gemini", providers)
        self.assertIn("openai", providers)
        self.assertIn("gpt-3.5-turbo", providers["openai"]["available_models"])

    def test_create_session_and_rbac_enforcement(self):
        """Assigned caregiver can create session for resident1, but gets 403 for resident2."""
        # Assigned resident -> 201 Created
        resp_ok = self.client.post(
            "/api/v1/chat/sessions",
            headers=self.cg1_headers,
            json={
                "resident_id": self.resident1.id,
                "title": "Sleep Consultation",
                "provider": "gemini",
                "model": "gemini-2.0-flash",
            },
        )
        self.assertEqual(resp_ok.status_code, 201)
        session_json = resp_ok.json()
        self.assertEqual(session_json["resident_id"], self.resident1.id)
        self.assertEqual(
            session_json["extra_metadata"]["provider"], "gemini"
        )

        # Unassigned resident -> 403 Forbidden
        resp_forbidden = self.client.post(
            "/api/v1/chat/sessions",
            headers=self.cg1_headers,
            json={
                "resident_id": self.resident2.id,
                "title": "Unauthorized Session",
            },
        )
        self.assertEqual(resp_forbidden.status_code, 403)

    def test_send_message_and_retrieve_history_flow(self):
        """POST /api/v1/chat/message should execute LangGraph, persist turns, and return response."""
        create_resp = self.client.post(
            "/api/v1/chat/sessions",
            headers=self.cg1_headers,
            json={
                "resident_id": self.resident1.id,
                "title": "Daily Routine Chat",
                "provider": "gemini",
            },
        )
        session_id = create_resp.json()["id"]

        # Send Turn 1 with Gemini
        msg_resp = self.client.post(
            "/api/v1/chat/message",
            headers=self.cg1_headers,
            json={
                "conversation_id": session_id,
                "message": "How can I improve my daily routine?",
                "provider": "gemini",
                "model": "gemini-2.0-flash",
            },
        )
        self.assertEqual(msg_resp.status_code, 200)
        turn_data = msg_resp.json()
        self.assertEqual(turn_data["provider"], "gemini")
        self.assertEqual(turn_data["model"], "gemini-2.0-flash")
        self.assertEqual(
            turn_data["user_message"]["content"],
            "How can I improve my daily routine?",
        )
        self.assertIn(
            "[gemini:gemini-2.0-flash]",
            turn_data["assistant_message"]["content"],
        )
        self.assertEqual(turn_data["token_usage"]["total_tokens"], 40)

        # Send Turn 2 switching to OpenAI gpt-3.5-turbo
        msg_resp2 = self.client.post(
            "/api/v1/chat/message",
            headers=self.cg1_headers,
            json={
                "conversation_id": session_id,
                "message": "Give me a tip for evening relaxation.",
                "provider": "openai",
                "model": "gpt-3.5-turbo",
            },
        )
        self.assertEqual(msg_resp2.status_code, 200)
        turn_data2 = msg_resp2.json()
        self.assertEqual(turn_data2["provider"], "openai")
        self.assertEqual(turn_data2["model"], "gpt-3.5-turbo")
        self.assertIn(
            "[openai:gpt-3.5-turbo]",
            turn_data2["assistant_message"]["content"],
        )

        # Retrieve history -> 4 messages in chronological order
        hist_resp = self.client.get(
            f"/api/v1/chat/sessions/{session_id}/history",
            headers=self.cg1_headers,
        )
        self.assertEqual(hist_resp.status_code, 200)
        history = hist_resp.json()
        self.assertEqual(len(history), 4)
        self.assertEqual(history[0]["role"], "user")
        self.assertEqual(history[1]["role"], "assistant")
        self.assertEqual(history[2]["role"], "user")
        self.assertEqual(history[3]["role"], "assistant")

        # Unassigned caregiver cannot view history -> 403 Forbidden
        unauth_hist = self.client.get(
            f"/api/v1/chat/sessions/{session_id}/history",
            headers=self.cg2_headers,
        )
        self.assertEqual(unauth_hist.status_code, 403)

    def test_emergency_message_triggers_safety_alert_in_api_response(self):
        """Emergency messages should populate safety.requires_caregiver_alert = True."""
        create_resp = self.client.post(
            "/api/v1/chat/sessions",
            headers=self.cg1_headers,
            json={"resident_id": self.resident1.id, "title": "Safety Test"},
        )
        session_id = create_resp.json()["id"]

        msg_resp = self.client.post(
            "/api/v1/chat/message",
            headers=self.cg1_headers,
            json={
                "conversation_id": session_id,
                "message": "I fell down in my room and hit my head!",
            },
        )
        self.assertEqual(msg_resp.status_code, 200)
        data = msg_resp.json()
        self.assertEqual(data["safety"]["risk_level"], "high_emergency")
        self.assertTrue(data["safety"]["requires_caregiver_alert"])
        self.assertIn("fall_or_injury", data["safety"]["flagged_categories"])

    def test_update_and_delete_chat_session(self):
        """PATCH and DELETE on /api/v1/chat/sessions/{id} should work as expected."""
        create_resp = self.client.post(
            "/api/v1/chat/sessions",
            headers=self.admin_headers,
            json={"resident_id": self.resident2.id, "title": "Initial"},
        )
        session_id = create_resp.json()["id"]

        patch_resp = self.client.patch(
            f"/api/v1/chat/sessions/{session_id}",
            headers=self.admin_headers,
            json={
                "title": "Renamed Session",
                "status": "archived",
                "provider": "openai",
                "model": "gpt-3.5-turbo",
            },
        )
        self.assertEqual(patch_resp.status_code, 200)
        updated = patch_resp.json()
        self.assertEqual(updated["title"], "Renamed Session")
        self.assertEqual(updated["status"], "archived")
        self.assertEqual(updated["extra_metadata"]["provider"], "openai")
        self.assertEqual(updated["extra_metadata"]["model"], "gpt-3.5-turbo")

        del_resp = self.client.delete(
            f"/api/v1/chat/sessions/{session_id}",
            headers=self.admin_headers,
        )
        self.assertEqual(del_resp.status_code, 204)


if __name__ == "__main__":
    unittest.main()

