"""Abstract base class for semantic text embedding providers."""

from abc import ABC, abstractmethod


class BaseEmbeddingProvider(ABC):
    """Abstract interface for text embedding providers (Gemini, OpenAI, Mock)."""

    provider_name: str
    dimension: int

    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        """Generate a dense vector embedding for a single text chunk."""
        pass

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate vector embeddings for a list of text chunks."""
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if the provider has valid credentials configured."""
        pass
