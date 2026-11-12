from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

from src.ai.exceptions import LLMConfigurationError, LLMModelNotSupportedError


@dataclass(frozen=True)
class ChatMessageInput:
    """Normalized conversational message turn passed to LLM providers."""

    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class LLMGenerationRequest:
    """Unified request payload for LLM generation across all providers."""

    messages: list[ChatMessageInput]
    system_prompt: str
    model: str | None = None
    temperature: float = 0.3
    max_tokens: int = 1024


@dataclass
class LLMGenerationResponse:
    """Unified response payload returned by LLM providers."""

    content: str
    provider: str
    model: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    latency_ms: float = 0.0
    finish_reason: str | None = None
    raw_metadata: dict[str, Any] = field(default_factory=dict)


class BaseLLMProvider(ABC):
    """Abstract base class defining the contract for all LLM providers."""

    provider_name: str
    default_model: str
    available_models: list[str]

    @abstractmethod
    def is_configured(self) -> bool:
        """Return True if the provider has valid API credentials configured."""
        raise NotImplementedError

    def ensure_configured(self) -> None:
        """Raise LLMConfigurationError if credentials are missing."""
        if not self.is_configured():
            raise LLMConfigurationError(
                f"LLM provider '{self.provider_name}' is not configured. "
                f"Please configure the corresponding API key in your environment."
            )

    def validate_model(self, requested_model: str | None = None) -> str:
        """Resolve and validate the model identifier for this provider."""
        if not requested_model or not requested_model.strip():
            return self.default_model

        cleaned = requested_model.strip()
        if cleaned not in self.available_models:
            raise LLMModelNotSupportedError(
                f"Model '{cleaned}' is not supported by provider '{self.provider_name}'. "
                f"Supported models: {', '.join(self.available_models)}"
            )
        return cleaned

    @abstractmethod
    def generate(self, request: LLMGenerationRequest) -> LLMGenerationResponse:
        """Execute a synchronous chat completion call."""
        raise NotImplementedError

    @abstractmethod
    def stream(self, request: LLMGenerationRequest) -> Iterator[str]:
        """Execute a streaming chat completion call yielding text chunks."""
        raise NotImplementedError

