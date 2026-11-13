"""Factory for managing embedding providers with testing overrides."""

from src.ai.embeddings.base import BaseEmbeddingProvider
from src.ai.embeddings.gemini_embedding import GeminiEmbeddingProvider
from src.ai.embeddings.openai_embedding import OpenAIEmbeddingProvider
from src.ai.exceptions import LLMModelNotSupportedError
from src.core.config import settings


class EmbeddingProviderFactory:
    """Instantiates embedding providers based on configuration or overrides."""

    _overrides: dict[str, BaseEmbeddingProvider] = {}

    @classmethod
    def register_override(cls, provider_name: str, provider: BaseEmbeddingProvider) -> None:
        cls._overrides[provider_name.lower().strip()] = provider

    @classmethod
    def clear_overrides(cls) -> None:
        cls._overrides.clear()

    @classmethod
    def get_provider(cls, name: str | None = None) -> BaseEmbeddingProvider:
        prov_key = (name or getattr(settings, "DEFAULT_EMBEDDING_PROVIDER", "gemini")).lower().strip()

        if prov_key in cls._overrides:
            return cls._overrides[prov_key]

        if prov_key == "gemini":
            return GeminiEmbeddingProvider()
        elif prov_key == "openai":
            return OpenAIEmbeddingProvider()
        else:
            raise LLMModelNotSupportedError(f"Unsupported embedding provider '{prov_key}'. Use 'gemini' or 'openai'.")
