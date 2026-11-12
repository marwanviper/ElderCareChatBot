"""Unit and integration tests for the Streamlit frontend HTTP client and service wrappers."""

import json
import unittest
from datetime import date

import httpx

from frontend.services.api_client import APIClient, APIError
from frontend.services.auth_service import AuthService
from frontend.services.care_service import CareService
from frontend.services.chat_service import ChatFrontendService


class TestFrontendClientAndServices(unittest.TestCase):
    """Verify APIClient, AuthService, CareService, and ChatFrontendService."""

    def test_api_client_injects_bearer_token_and_cleans_params(self) -> None:
        """APIClient should inject Authorization Bearer header and drop None query params."""
        captured_request: httpx.Request | None = None

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal captured_request
            captured_request = request
            return httpx.Response(200, json=[{"id": 1, "name": "Anna Müller"}])

        transport = httpx.MockTransport(handler)
        client = APIClient(base_url="http://testserver/api/v1", transport=transport)
        care_svc = CareService(client)

        res = care_svc.list_residents(token="jwt-secret-token", skip=0, limit=50)
        self.assertEqual(len(res), 1)
        self.assertIsNotNone(captured_request)
        assert captured_request is not None
        self.assertEqual(
            captured_request.headers.get("Authorization"),
            "Bearer jwt-secret-token",
        )
        self.assertIn("limit=50", str(captured_request.url))

    def test_api_client_translates_http_errors_into_api_error(self) -> None:
        """APIClient should raise structured APIError on 401/403/422 responses."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                401,
                json={"detail": "Incorrect email or password"},
            )

        transport = httpx.MockTransport(handler)
        client = APIClient(base_url="http://testserver/api/v1", transport=transport)
        auth_svc = AuthService(client)

        with self.assertRaises(APIError) as ctx:
            auth_svc.login("wrong@eldercare.org", "badpass")

        self.assertEqual(ctx.exception.status_code, 401)
        self.assertIn("Incorrect email or password", ctx.exception.message)

    def test_care_and_chat_services_payload_serialization(self) -> None:
        """CareService and ChatFrontendService should format JSON payloads accurately."""
        requests_log: list[tuple[str, str, dict]] = []

        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content.decode()) if request.content else {}
            requests_log.append((request.method, request.url.path, body))
            if request.method == "DELETE":
                return httpx.Response(204)
            return httpx.Response(201, json={"id": 10, **body})

        transport = httpx.MockTransport(handler)
        client = APIClient(base_url="http://testserver/api/v1", transport=transport)
        care_svc = CareService(client)
        chat_svc = ChatFrontendService(client)

        # 1. Create resident with date object
        care_svc.create_resident(
            token="tok",
            name="Arthur Pendelton",
            date_of_birth=date(1940, 5, 20),
            room_number="102A",
        )
        self.assertEqual(requests_log[-1][0], "POST")
        self.assertEqual(requests_log[-1][1], "/api/v1/residents")
        self.assertEqual(requests_log[-1][2]["date_of_birth"], "1940-05-20")

        # 2. Create chat session with Gemini
        chat_svc.create_session(
            token="tok",
            resident_id=10,
            title="Morning Check-in",
            provider="gemini",
            model="gemini-2.0-flash",
        )
        self.assertEqual(requests_log[-1][1], "/api/v1/chat/sessions")
        self.assertEqual(requests_log[-1][2]["provider"], "gemini")

        # 3. Send message with OpenAI GPT-3.5 override
        chat_svc.send_message(
            token="tok",
            conversation_id=10,
            content="Good morning!",
            provider="openai",
            model="gpt-3.5-turbo",
            temperature=0.3,
        )
        self.assertEqual(requests_log[-1][1], "/api/v1/chat/message")
        self.assertEqual(requests_log[-1][2]["message"], "Good morning!")
        self.assertEqual(requests_log[-1][2]["provider"], "openai")
        self.assertEqual(requests_log[-1][2]["model"], "gpt-3.5-turbo")

        # 4. Delete session (204 No Content)
        result = chat_svc.delete_session(token="tok", session_id=10)
        self.assertIsNone(result)

    def test_frontend_modules_import_cleanly(self) -> None:
        """All frontend views, components, and app entry point should import without error."""
        import frontend.app  # noqa: F401
        import frontend.components.sidebar  # noqa: F401
        import frontend.components.ui_cards  # noqa: F401
        import frontend.views.care_goals_view  # noqa: F401
        import frontend.views.care_reports_view  # noqa: F401
        import frontend.views.chat_view  # noqa: F401
        import frontend.views.conversations_view  # noqa: F401
        import frontend.views.dashboard_view  # noqa: F401
        import frontend.views.incidents_view  # noqa: F401
        import frontend.views.login_view  # noqa: F401
        import frontend.views.residents_view  # noqa: F401


if __name__ == "__main__":
    unittest.main()

