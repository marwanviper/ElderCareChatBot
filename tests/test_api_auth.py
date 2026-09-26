import unittest
from tests.test_api_base import ApiTestCase


class TestApiAuth(ApiTestCase):
    """Test suite for authentication endpoints (/api/v1/auth/*)."""

    def test_register_user_success(self):
        """Test registration of a new caregiver user."""
        payload = {
            "name": "Sarah Nurse",
            "email": "sarah.nurse@eldercare.test",
            "password": "SecurePassword123!",
            "role": "caregiver",
        }
        response = self.client.post("/api/v1/auth/register", json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["name"], "Sarah Nurse")
        self.assertEqual(data["email"], "sarah.nurse@eldercare.test")
        self.assertEqual(data["role"], "caregiver")
        self.assertIn("id", data)
        self.assertNotIn("password", data)
        self.assertNotIn("password_hash", data)

    def test_register_duplicate_email(self):
        """Test that registering an existing email returns 409 Conflict."""
        self.create_test_user(email="duplicate@eldercare.test")
        payload = {
            "name": "Another User",
            "email": "duplicate@eldercare.test",
            "password": "SecurePassword123!",
            "role": "caregiver",
        }
        response = self.client.post("/api/v1/auth/register", json=payload)
        self.assertEqual(response.status_code, 409)
        self.assertIn("already exists", response.json()["detail"])

    def test_register_validation_error(self):
        """Test registration with invalid payload returns 422 Unprocessable Entity."""
        # Invalid email format and too short password
        payload = {
            "name": "Bad User",
            "email": "not-an-email",
            "password": "short",
            "role": "caregiver",
        }
        response = self.client.post("/api/v1/auth/register", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_oauth2_form_login_success(self):
        """Test standard OAuth2 form login (/api/v1/auth/login)."""
        self.create_test_user(
            email="login_form@eldercare.test",
            password="StrongPassword123!",
            role="caregiver",
        )
        response = self.client.post(
            "/api/v1/auth/login",
            data={
                "username": "login_form@eldercare.test",
                "password": "StrongPassword123!",
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["token_type"], "bearer")

    def test_oauth2_form_login_invalid_credentials(self):
        """Test OAuth2 form login with incorrect password returns 401."""
        self.create_test_user(
            email="login_fail@eldercare.test",
            password="CorrectPassword123!",
        )
        response = self.client.post(
            "/api/v1/auth/login",
            data={
                "username": "login_fail@eldercare.test",
                "password": "WrongPassword!",
            },
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("Incorrect email or password", response.json()["detail"])

    def test_json_login_success(self):
        """Test REST JSON login endpoint (/api/v1/auth/login/json)."""
        self.create_test_user(
            email="login_json@eldercare.test",
            password="StrongPassword123!",
            role="admin",
        )
        response = self.client.post(
            "/api/v1/auth/login/json",
            json={
                "email": "login_json@eldercare.test",
                "password": "StrongPassword123!",
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["token_type"], "bearer")

    def test_json_login_invalid_password(self):
        """Test JSON login with invalid password returns 401."""
        self.create_test_user(
            email="json_invalid@eldercare.test",
            password="Password123!",
        )
        response = self.client.post(
            "/api/v1/auth/login/json",
            json={
                "email": "json_invalid@eldercare.test",
                "password": "IncorrectPassword!",
            },
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("Incorrect email or password", response.json()["detail"])

    def test_get_current_user_me(self):
        """Test GET /api/v1/auth/me with valid Bearer token."""
        user = self.create_test_user(
            name="Alice Walker",
            email="alice.walker@eldercare.test",
            role="caregiver",
        )
        headers = self.get_auth_headers(user)
        response = self.client.get("/api/v1/auth/me", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], user.id)
        self.assertEqual(data["email"], "alice.walker@eldercare.test")
        self.assertEqual(data["name"], "Alice Walker")
        self.assertEqual(data["role"], "caregiver")

    def test_get_me_unauthorized_without_token(self):
        """Test GET /api/v1/auth/me without token returns 401."""
        response = self.client.get("/api/v1/auth/me")
        self.assertEqual(response.status_code, 401)

    def test_get_me_invalid_token(self):
        """Test GET /api/v1/auth/me with malformed token returns 401."""
        headers = {"Authorization": "Bearer invalid.jwt.token"}
        response = self.client.get("/api/v1/auth/me", headers=headers)
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
