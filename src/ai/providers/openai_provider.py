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


class OpenAIProvider(BaseLLMProvider):
    """OpenAI LLM provider implementation supporting GPT-3.5-Turbo and compatible models."""

    provider_name = "openai"

    def __init__(self, api_key: str | None = None, default_model: str | None = None):
        if api_key is not None:
            raw_key = api_key
        else:
            raw_key = settings.OPENAI_API_KEY or Settings().OPENAI_API_KEY
        self._api_key = (
            raw_key.strip().strip('"').strip("'") if raw_key else None
        )
        self.default_model = (
            default_model or settings.OPENAI_DEFAULT_MODEL or "gpt-3.5-turbo"
        )
        base_models = [
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-0125",
            "gpt-4o-mini",
        ]
        if self.default_model not in base_models:
            base_models.insert(0, self.default_model)
        self.available_models = base_models

    def is_configured(self) -> bool:
        return bool(
            self._api_key
            and self._api_key.strip()
            and self._api_key != "your-openai-api-key"
        )

    def _get_client(self):
        self.ensure_configured()
        try:
            from openai import OpenAI

            return OpenAI(api_key=self._api_key)
        except ImportError as exc:
            raise LLMConfigurationError(
                "openai package is not installed."
            ) from exc

    @staticmethod
    def _build_messages(
        system_prompt: str, messages: list[ChatMessageInput]
    ) -> list[dict[str, str]]:
        """Assemble OpenAI chat completion messages with leading system prompt."""
        payload: list[dict[str, str]] = [
            {"role": "system", "content": system_prompt}
        ]
        for msg in messages:
            if msg.role == "system":
                continue
            role = "assistant" if msg.role == "assistant" else "user"
            payload.append({"role": role, "content": msg.content})
        return payload

    def generate(self, request: LLMGenerationRequest) -> LLMGenerationResponse:
        self.ensure_configured()
        model_name = self.validate_model(request.model)
        client = self._get_client()

        messages_payload = self._build_messages(
            request.system_prompt, request.messages
        )
        if len(messages_payload) <= 1:
            raise LLMProviderError("Cannot generate OpenAI response without user messages.")

        start_time = time.perf_counter()
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=messages_payload,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )
        except Exception as exc:
            err_str = str(exc)
            exc_name = type(exc).__name__
            logger.error(
                "OpenAI API error with model %s: %s - %s",
                model_name,
                exc_name,
                err_str,
            )
            if "RateLimitError" in exc_name or "429" in err_str or "quota" in err_str.lower():
                raise LLMRateLimitError(
                    "OpenAI API rate limit or quota exceeded. Please try again shortly."
                ) from exc
            if "AuthenticationError" in exc_name or "invalid_api_key" in err_str.lower() or "401" in err_str:
                raise LLMConfigurationError(
                    "Invalid OpenAI API key. Please verify OPENAI_API_KEY in .env."
                ) from exc
            raise LLMProviderError(
                f"OpenAI API request failed ({exc_name}): {err_str}"
            ) from exc

        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        choices = getattr(response, "choices", None)
        if not choices or len(choices) == 0:
            raise LLMProviderError("OpenAI returned no completion choices.")

        first_choice = choices[0]
        message_obj = getattr(first_choice, "message", None)
        text_content = getattr(message_obj, "content", None) if message_obj else None
        if not text_content or not text_content.strip():
            raise LLMProviderError("OpenAI returned an empty message content.")

        usage = getattr(response, "usage", None)
        prompt_tokens = getattr(usage, "prompt_tokens", None) if usage else None
        completion_tokens = (
            getattr(usage, "completion_tokens", None) if usage else None
        )
        total_tokens = getattr(usage, "total_tokens", None) if usage else None
        finish_reason = getattr(first_choice, "finish_reason", "stop")

        return LLMGenerationResponse(
            content=text_content.strip(),
            provider=self.provider_name,
            model=getattr(response, "model", model_name) or model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            finish_reason=str(finish_reason) if finish_reason else "stop",
        )

    def stream(self, request: LLMGenerationRequest) -> Iterator[str]:
        self.ensure_configured()
        model_name = self.validate_model(request.model)
        client = self._get_client()

        messages_payload = self._build_messages(
            request.system_prompt, request.messages
        )
        try:
            stream_resp = client.chat.completions.create(
                model=model_name,
                messages=messages_payload,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stream=True,
            )
            for chunk in stream_resp:
                choices = getattr(chunk, "choices", None)
                if choices and len(choices) > 0:
                    delta = getattr(choices[0], "delta", None)
                    content = getattr(delta, "content", None) if delta else None
                    if content:
                        yield content
        except Exception as exc:
            err_str = str(exc)
            exc_name = type(exc).__name__
            if "RateLimitError" in exc_name or "429" in err_str:
                raise LLMRateLimitError(
                    "OpenAI streaming rate limit exceeded."
                ) from exc
            raise LLMProviderError(
                f"OpenAI streaming failed: {exc_name}"
            ) from exc

