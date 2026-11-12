class AIError(Exception):
    """Base exception for AI and conversational orchestration errors."""

    def __init__(self, message: str, error_code: str = "ai_error"):
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class LLMConfigurationError(AIError):
    """Raised when an LLM provider is missing API keys or required configuration."""

    def __init__(self, message: str):
        super().__init__(message, error_code="llm_configuration_error")


class LLMModelNotSupportedError(AIError):
    """Raised when an unsupported provider or model identifier is requested."""

    def __init__(self, message: str):
        super().__init__(message, error_code="llm_model_not_supported")


class LLMRateLimitError(AIError):
    """Raised when the upstream LLM provider rejects a request due to rate limits or quota."""

    def __init__(self, message: str):
        super().__init__(message, error_code="llm_rate_limit_error")


class LLMProviderError(AIError):
    """Raised when an upstream LLM provider call fails or returns an invalid response."""

    def __init__(self, message: str):
        super().__init__(message, error_code="llm_provider_error")


class ChatValidationError(AIError):
    """Raised when user message input or conversation state fails validation."""

    def __init__(self, message: str):
        super().__init__(message, error_code="chat_validation_error")

