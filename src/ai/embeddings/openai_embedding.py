"""OpenAI semantic embedding provider."""

from src.ai.embeddings.base import BaseEmbeddingProvider
from src.ai.exceptions import LLMConfigurationError, LLMProviderError
from src.core.config import Settings, settings
from src.core.logging import logger


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """Generates embeddings using OpenAI text-embedding-3-small (768 dimensions)."""

    provider_name = "openai"
    dimension = 768
    model_name = "text-embedding-3-small"

    def __init__(self, api_key: str | None = None):
        if api_key is not None:
            raw_key = api_key
        else:
            raw_key = settings.OPENAI_API_KEY or Settings().OPENAI_API_KEY
        self._api_key = raw_key.strip().strip('"').strip("'") if raw_key else None

    def is_configured(self) -> bool:
        return bool(
            self._api_key
            and self._api_key.strip()
            and self._api_key != "your-openai-api-key"
        )

    def _get_client(self):
        if not self.is_configured():
            raise LLMConfigurationError(
                "OPENAI_API_KEY is not configured for text embeddings."
            )
        try:
            from openai import OpenAI
            return OpenAI(api_key=self._api_key)
        except ImportError as exc:
            raise LLMConfigurationError("openai package is not installed.") from exc

    def embed_text(self, text: str) -> list[float]:
        batch_res = self.embed_batch([text])
        if not batch_res:
            raise LLMProviderError("OpenAI returned empty embedding.")
        return batch_res[0]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        client = self._get_client()
        clean_texts = [t.strip() for t in texts]

        try:
            response = client.embeddings.create(
                model=self.model_name,
                input=clean_texts,
                dimensions=self.dimension,
            )
            return [list(item.embedding) for item in response.data]
        except Exception as exc:
            logger.error("OpenAI embeddings error: %s", type(exc).__name__)
            raise LLMProviderError(f"Failed to generate OpenAI embeddings: {exc}") from exc
