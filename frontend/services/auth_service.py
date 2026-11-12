"""Authentication and User Management service wrapper for the Streamlit frontend."""

from typing import Any

from frontend.services.api_client import APIClient


class AuthService:
    """Service methods for `/api/v1/auth` and `/api/v1/users` endpoints."""

    def __init__(self, client: APIClient | None = None) -> None:
        self.client = client or APIClient()

    def login(self, email: str, password: str) -> dict[str, Any]:
        """Authenticate user via `/api/v1/auth/login/json` and return JWT token payload."""
        return self.client.post(
            "/auth/login/json",
            json={"email": email.strip(), "password": password},
        )

    def register(
        self,
        name: str,
        email: str,
        password: str,
        role: str = "caregiver",
    ) -> dict[str, Any]:
        """Register a new user account via `/api/v1/auth/register`."""
        return self.client.post(
            "/auth/register",
            json={
                "name": name.strip(),
                "email": email.strip(),
                "password": password,
                "role": role,
            },
        )

    def get_current_user(self, token: str) -> dict[str, Any]:
        """Retrieve the profile of the currently authenticated user via `/api/v1/auth/me`."""
        return self.client.get("/auth/me", token=token)

    def list_users(
        self,
        token: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List all registered users (Admin only)."""
        return self.client.get(
            "/users",
            token=token,
            params={"skip": skip, "limit": limit},
        )

