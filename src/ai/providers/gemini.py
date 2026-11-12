import time
from collections.abc import Iterator

from src.ai.exceptions import (
    LLMConfigurationError,
    LLMProviderError,
    LLMRateLimitError,
)
from src.ai.providers.base import (
    BaseLLMProvider,
    ChatMessageInput,
    LLMGenerationRequest,
    LLMGenerationResponse,
)
from src.core.config import Settings, settings
from src.core.logging import logger


class GeminiProvider(BaseLLMProvider):
    """Google Gemini LLM provider implementation using the official google-genai SDK."""

    provider_name = "gemini"

    def __init__(self, api_key: str | None = None, default_model: str | None = None):
        if api_key is not None:
            raw_key = api_key
        else:
            raw_key = settings.GEMINI_API_KEY or Settings().GEMINI_API_KEY
        self._api_key = (
            raw_key.strip().strip('"').strip("'") if raw_key else None
        )
        self.default_model = (
            default_model or settings.GEMINI_DEFAULT_MODEL or "gemini-3.5-flash"
        )
        base_models = [
            "gemini-3.5-flash",
            "gemini-2.5-flash",
            "gemini-1.5-flash",
            "gemini-1.5-pro",
        ]
        if self.default_model not in base_models:
            base_models.insert(0, self.default_model)
        self.available_models = base_models

    def is_configured(self) -> bool:
        return bool(
            self._api_key
            and self._api_key.strip()
            and self._api_key != "your-google-gemini-api-key"
        )

    def _get_client(self):
        self.ensure_configured()
        try:
            from google import genai

            return genai.Client(api_key=self._api_key)
        except ImportError as exc:
            raise LLMConfigurationError(
                "google-genai package is not installed."
            ) from exc

    @staticmethod
    def _build_contents(messages: list[ChatMessageInput]) -> list[dict]:
        """Convert normalized ChatMessageInput list into Gemini content turns."""
        contents = []
        for msg in messages:
            if msg.role == "system":
                continue
            gemini_role = "model" if msg.role == "assistant" else "user"
            contents.append(
                {
                    "role": gemini_role,
                    "parts": [{"text": msg.content}],
                }
            )
        return contents

    def generate(self, request: LLMGenerationRequest) -> LLMGenerationResponse:
        self.ensure_configured()
        model_name = self.validate_model(request.model)
        client = self._get_client()

        contents = self._build_contents(request.messages)
        if not contents:
            raise LLMProviderError("Cannot generate Gemini response with empty message list.")

        config_dict = {
            "system_instruction": request.system_prompt,
            "temperature": request.temperature,
            "max_output_tokens": request.max_tokens,
        }

        start_time = time.perf_counter()
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config_dict,
            )
        except Exception as exc:
            err_str = str(exc)
            logger.error(
                "Gemini API error with model %s: %s - %s",
                model_name,
                type(exc).__name__,
                err_str,
            )
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str.upper() or "quota" in err_str.lower():
                raise LLMRateLimitError(
                    "Google Gemini API rate limit or quota exceeded. Please try again shortly."
                ) from exc
            if "API_KEY_INVALID" in err_str.upper() or "API KEY NOT VALID" in err_str.upper():
                raise LLMConfigurationError(
                    "Invalid Google Gemini API key (API_KEY_INVALID). "
                    "Google AI Studio keys start with 'AIza...' — please verify GEMINI_API_KEY in .env."
                ) from exc
            raise LLMProviderError(
                f"Google Gemini API request failed ({type(exc).__name__}): {err_str}"
            ) from exc

        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        text_content = getattr(response, "text", None)
        if not text_content or not text_content.strip():
            raise LLMProviderError("Google Gemini returned an empty response.")

        usage = getattr(response, "usage_metadata", None)
        prompt_tokens = getattr(usage, "prompt_token_count", None) if usage else None
        completion_tokens = (
            getattr(usage, "candidates_token_count", None) if usage else None
        )
        total_tokens = getattr(usage, "total_token_count", None) if usage else None

        finish_reason = "STOP"
        candidates = getattr(response, "candidates", None)
        if candidates and len(candidates) > 0:
            fr = getattr(candidates[0], "finish_reason", None)
            if fr is not None:
                finish_reason = str(getattr(fr, "name", fr))

        return LLMGenerationResponse(
            content=text_content.strip(),
            provider=self.provider_name,
            model=model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            finish_reason=finish_reason,
        )

    def stream(self, request: LLMGenerationRequest) -> Iterator[str]:
        self.ensure_configured()
        model_name = self.validate_model(request.model)
        client = self._get_client()

        contents = self._build_contents(request.messages)
        config_dict = {
            "system_instruction": request.system_prompt,
            "temperature": request.temperature,
            "max_output_tokens": request.max_tokens,
        }

        try:
            response_stream = client.models.generate_content_stream(
                model=model_name,
                contents=contents,
                config=config_dict,
            )
            for chunk in response_stream:
                chunk_text = getattr(chunk, "text", None)
                if chunk_text:
                    yield chunk_text
        except Exception as exc:
            err_str = str(exc)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str.upper():
                raise LLMRateLimitError(
                    "Google Gemini streaming rate limit exceeded."
                ) from exc
            raise LLMProviderError(
                f"Google Gemini streaming failed: {type(exc).__name__}"
            ) from exc

