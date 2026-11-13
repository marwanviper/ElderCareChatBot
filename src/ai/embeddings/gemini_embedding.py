"""Google Gemini semantic embedding provider."""

from src.ai.embeddings.base import BaseEmbeddingProvider
from src.ai.exceptions import LLMConfigurationError, LLMProviderError
from src.core.config import Settings, settings
from src.core.logging import logger


class GeminiEmbeddingProvider(BaseEmbeddingProvider):
    """Generates embeddings using Google GenAI gemini-embedding-001 (768 dimensions)."""

    provider_name = "gemini"
    dimension = 768
    model_name = "gemini-embedding-001"

    def __init__(self, api_key: str | None = None):
        if api_key is not None:
            raw_key = api_key
        else:
            raw_key = settings.GEMINI_API_KEY or Settings().GEMINI_API_KEY
        self._api_key = raw_key.strip().strip('"').strip("'") if raw_key else None

    def is_configured(self) -> bool:
        return bool(
            self._api_key
            and self._api_key.strip()
            and self._api_key != "your-google-gemini-api-key"
        )

    def _get_client(self):
        if not self.is_configured():
            raise LLMConfigurationError(
                "GEMINI_API_KEY is not configured for text embeddings."
            )
        try:
            from google import genai
            return genai.Client(api_key=self._api_key)
        except ImportError as exc:
            raise LLMConfigurationError("google-genai package is not installed.") from exc

    def embed_text(self, text: str) -> list[float]:
        """Embed a single string."""
        batch_res = self.embed_batch([text])
        if not batch_res:
            raise LLMProviderError("Gemini returned empty embedding.")
        return batch_res[0]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of strings."""
        if not texts:
            return []

        client = self._get_client()
        clean_texts = [t.strip() for t in texts]

        try:
            results = []
            for t in clean_texts:
                response = client.models.embed_content(
                    model=self.model_name,
                    contents=t,
                    config={"output_dimensionality": self.dimension},
                )
                vals = None
                if hasattr(response, "embeddings") and response.embeddings:
                    vals = response.embeddings[0].values
                elif hasattr(response, "embedding") and hasattr(response.embedding, "values"):
                    vals = response.embedding.values

                if not vals:
                    raise LLMProviderError("No embedding values returned by Gemini API.")
                results.append(list(vals))
            return results
        except Exception as exc:
            logger.error("Gemini embed_content error: %s", type(exc).__name__)
            raise LLMProviderError(f"Failed to generate Gemini embeddings: {exc}") from exc
