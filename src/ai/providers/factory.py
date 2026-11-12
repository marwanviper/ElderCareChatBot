from typing import Any

from src.ai.exceptions import LLMModelNotSupportedError
from src.ai.providers.base import BaseLLMProvider
from src.ai.providers.gemini import GeminiProvider
from src.ai.providers.openai_provider import OpenAIProvider
from src.core.config import settings


class LLMProviderFactory:
    """Factory responsible for instantiating and inspecting supported LLM providers."""

    _overrides: dict[str, BaseLLMProvider] = {}

    @classmethod
    def register_override(
        cls, provider_name: str, provider_instance: BaseLLMProvider
    ) -> None:
        """Register a provider instance override (used for isolated testing)."""
        cls._overrides[provider_name.lower().strip()] = provider_instance

    @classmethod
    def clear_overrides(cls) -> None:
        """Clear any registered test provider overrides."""
        cls._overrides.clear()

    @classmethod
    def get_provider(cls, provider_name: str | None = None) -> BaseLLMProvider:
        """Instantiate and return the requested LLM provider."""
        resolved_name = (
            provider_name.strip().lower()
            if provider_name and provider_name.strip()
            else settings.DEFAULT_LLM_PROVIDER.strip().lower()
        )

        if resolved_name in cls._overrides:
            return cls._overrides[resolved_name]

        if resolved_name == "gemini":
            return GeminiProvider()
        if resolved_name == "openai":
            return OpenAIProvider()

        raise LLMModelNotSupportedError(
            f"Unsupported LLM provider '{resolved_name}'. "
            f"Supported providers are: gemini, openai."
        )

    @classmethod
    def list_providers_info(cls) -> list[dict[str, Any]]:
        """Return metadata and configuration readiness for all supported providers."""
        providers: list[BaseLLMProvider] = [
            cls.get_provider("gemini"),
            cls.get_provider("openai"),
        ]
        return [
            {
                "provider": p.provider_name,
                "default_model": p.default_model,
                "available_models": p.available_models,
                "is_configured": p.is_configured(),
            }
            for p in providers
        ]

