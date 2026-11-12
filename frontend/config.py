"""Configuration settings for the ElderCareChatBot Streamlit frontend."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class FrontendConfig:
    """Immutable configuration for the Streamlit client."""

    API_BASE_URL: str = os.getenv("ELDERCARE_API_URL", "http://127.0.0.1:8000").rstrip("/")
    API_V1_PREFIX: str = "/api/v1"
    REQUEST_TIMEOUT_SECONDS: float = float(os.getenv("ELDERCARE_HTTP_TIMEOUT", "45.0"))
    APP_TITLE: str = "ElderCare AI — Care Management & Companion Platform"
    APP_ICON: str = "🏥"

    @property
    def api_v1_url(self) -> str:
        """Return full base URL for v1 API endpoints."""
        return f"{self.API_BASE_URL}{self.API_V1_PREFIX}"


frontend_config = FrontendConfig()

