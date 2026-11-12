import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.ai.exceptions import (
    LLMConfigurationError,
    LLMModelNotSupportedError,
    LLMProviderError,
    LLMRateLimitError,
)
from src.ai.providers.base import ChatMessageInput, LLMGenerationRequest
from src.ai.providers.factory import LLMProviderFactory
from src.ai.providers.gemini import GeminiProvider
from src.ai.providers.openai_provider import OpenAIProvider


class TestAIProviders(unittest.TestCase):
    """Unit tests for GeminiProvider, OpenAIProvider, and LLMProviderFactory."""

    def tearDown(self):
        LLMProviderFactory.clear_overrides()

    def test_factory_returns_expected_providers(self):
        """Factory should instantiate GeminiProvider and OpenAIProvider."""
        gemini = LLMProviderFactory.get_provider("gemini")
        openai_prov = LLMProviderFactory.get_provider("openai")

        self.assertIsInstance(gemini, GeminiProvider)
        self.assertIsInstance(openai_prov, OpenAIProvider)
        self.assertEqual(gemini.provider_name, "gemini")
        self.assertEqual(openai_prov.provider_name, "openai")
        self.assertIn("gpt-3.5-turbo", openai_prov.available_models)
        self.assertIn("gemini-3.5-flash", gemini.available_models)
        self.assertNotIn("gemini-2.0-flash", gemini.available_models)

    def test_factory_rejects_unknown_provider(self):
        """Factory should raise LLMModelNotSupportedError for unknown providers."""
        with self.assertRaises(LLMModelNotSupportedError):
            LLMProviderFactory.get_provider("unknown_vendor")

    def test_provider_missing_api_key_raises_configuration_error(self):
        """Unconfigured providers must raise LLMConfigurationError before calling APIs."""
        gemini = GeminiProvider(api_key="")
        self.assertFalse(gemini.is_configured())

        req = LLMGenerationRequest(
            messages=[ChatMessageInput(role="user", content="Hello")],
            system_prompt="System prompt",
        )
        with self.assertRaises(LLMConfigurationError):
            gemini.generate(req)

        openai_prov = OpenAIProvider(api_key="your-openai-api-key")
        self.assertFalse(openai_prov.is_configured())
        with self.assertRaises(LLMConfigurationError):
            openai_prov.generate(req)

    def test_validate_model_rejects_unsupported_model(self):
        """Providers should validate model identifiers against available_models."""
        gemini = GeminiProvider(api_key="test-key")
        self.assertEqual(gemini.validate_model(None), "gemini-3.5-flash")
        self.assertEqual(gemini.validate_model("gemini-1.5-flash"), "gemini-1.5-flash")

        with self.assertRaises(LLMModelNotSupportedError):
            gemini.validate_model("gpt-4-nonexistent")

        openai_prov = OpenAIProvider(api_key="test-key")
        self.assertEqual(openai_prov.validate_model(None), "gpt-3.5-turbo")
        self.assertEqual(openai_prov.validate_model("gpt-3.5-turbo"), "gpt-3.5-turbo")

        with self.assertRaises(LLMModelNotSupportedError):
            openai_prov.validate_model("claude-3-opus")

    def test_gemini_generate_success_with_mock_client(self):
        """GeminiProvider.generate should format turns and extract token usage properly."""
        gemini = GeminiProvider(api_key="fake-gemini-key")

        mock_client = MagicMock()
        mock_response = SimpleNamespace(
            text="Hello! Remember to drink a glass of water this morning.",
            usage_metadata=SimpleNamespace(
                prompt_token_count=45,
                candidates_token_count=12,
                total_token_count=57,
            ),
            candidates=[
                SimpleNamespace(finish_reason=SimpleNamespace(name="STOP"))
            ],
        )
        mock_client.models.generate_content.return_value = mock_response

        with patch.object(gemini, "_get_client", return_value=mock_client):
            req = LLMGenerationRequest(
                messages=[
                    ChatMessageInput(role="user", content="Good morning!"),
                ],
                system_prompt="You are a caring companion.",
                model="gemini-3.5-flash",
            )
            res = gemini.generate(req)

        self.assertEqual(res.provider, "gemini")
        self.assertEqual(res.model, "gemini-3.5-flash")
        self.assertIn("drink a glass of water", res.content)
        self.assertEqual(res.prompt_tokens, 45)
        self.assertEqual(res.completion_tokens, 12)
        self.assertEqual(res.total_tokens, 57)
        self.assertEqual(res.finish_reason, "STOP")

    def test_openai_generate_success_with_mock_client(self):
        """OpenAIProvider.generate should call gpt-3.5-turbo and extract usage metrics."""
        openai_prov = OpenAIProvider(api_key="fake-openai-key")

        mock_client = MagicMock()
        mock_response = SimpleNamespace(
            model="gpt-3.5-turbo-0125",
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content="A gentle walk after breakfast can help you feel refreshed."
                    ),
                    finish_reason="stop",
                )
            ],
            usage=SimpleNamespace(
                prompt_tokens=60,
                completion_tokens=15,
                total_tokens=75,
            ),
        )
        mock_client.chat.completions.create.return_value = mock_response

        with patch.object(openai_prov, "_get_client", return_value=mock_client):
            req = LLMGenerationRequest(
                messages=[
                    ChatMessageInput(role="user", content="Any morning tips?"),
                ],
                system_prompt="You are a caring companion.",
                model="gpt-3.5-turbo",
            )
            res = openai_prov.generate(req)

        self.assertEqual(res.provider, "openai")
        self.assertEqual(res.model, "gpt-3.5-turbo-0125")
        self.assertIn("gentle walk", res.content)
        self.assertEqual(res.prompt_tokens, 60)
        self.assertEqual(res.completion_tokens, 15)
        self.assertEqual(res.total_tokens, 75)
        self.assertEqual(res.finish_reason, "stop")

    def test_provider_rate_limit_error_translation(self):
        """Both providers should translate 429/rate-limit exceptions into LLMRateLimitError."""
        openai_prov = OpenAIProvider(api_key="fake-openai-key")
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("Error 429: Rate limit reached")

        with patch.object(openai_prov, "_get_client", return_value=mock_client):
            req = LLMGenerationRequest(
                messages=[ChatMessageInput(role="user", content="Hi")],
                system_prompt="System",
            )
            with self.assertRaises(LLMRateLimitError):
                openai_prov.generate(req)


if __name__ == "__main__":
    unittest.main()

