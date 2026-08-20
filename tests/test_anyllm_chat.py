import unittest
from unittest.mock import patch

from models.provider_config import ProviderConfig
from providers.anyllm_chat import (
    AnyLLMChatProvider,
    _require_supported_provider,
)


class TestRequireSupportedProvider(unittest.TestCase):
    @patch("providers.anyllm_chat.ProviderFactory.get_supported_providers")
    def test_returns_provider_when_supported(self, mock_supported) -> None:
        mock_supported.return_value = ["deepseek", "openai"]
        self.assertEqual(_require_supported_provider("deepseek"), "deepseek")

    @patch("providers.anyllm_chat.ProviderFactory.get_supported_providers")
    def test_raises_when_unsupported(self, mock_supported) -> None:
        mock_supported.return_value = ["deepseek", "openai"]
        with self.assertRaises(RuntimeError) as ctx:
            _require_supported_provider("dashscope")
        self.assertIn("不在 any-llm 支持列表中", str(ctx.exception))
        self.assertNotIn("OpenAI 兼容", str(ctx.exception))


class TestAnyLLMChatProvider(unittest.TestCase):
    @patch("providers.anyllm_chat.ProviderFactory.get_supported_providers")
    def test_deepseek_uses_configured_provider(self, mock_supported) -> None:
        mock_supported.return_value = ["deepseek", "openai"]
        provider = AnyLLMChatProvider(
            ProviderConfig(provider_name="deepseek", api_key="sk-test", default_model="deepseek-v4-pro")
        )
        self.assertEqual(provider._anyllm_provider_key, "deepseek")
        self.assertEqual(provider._resolve_model(None), "deepseek/deepseek-v4-pro")

    @patch("providers.anyllm_chat.ProviderFactory.get_supported_providers")
    def test_openai_provider_uses_configured_provider(self, mock_supported) -> None:
        mock_supported.return_value = ["deepseek", "openai"]
        provider = AnyLLMChatProvider(
            ProviderConfig(
                provider_name="openai",
                api_key="sk-test",
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                default_model="qwen3.7-max",
            )
        )
        self.assertEqual(provider._anyllm_provider_key, "openai")
        self.assertEqual(provider._resolve_model(None), "openai/qwen3.7-max")

    @patch("providers.anyllm_chat.ProviderFactory.get_supported_providers")
    def test_unsupported_provider_fails_on_init(self, mock_supported) -> None:
        mock_supported.return_value = ["deepseek", "openai"]
        with self.assertRaises(RuntimeError):
            AnyLLMChatProvider(
                ProviderConfig(
                    provider_name="dashscope",
                    api_key="sk-test",
                    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                    default_model="qwen3.7-max",
                )
            )

    @patch("providers.anyllm_chat.ProviderFactory.get_supported_providers")
    def test_model_with_prefix_validates_provider(self, mock_supported) -> None:
        mock_supported.return_value = ["deepseek", "openai"]
        provider = AnyLLMChatProvider(
            ProviderConfig(provider_name="deepseek", api_key="sk-test", default_model="deepseek-v4-pro")
        )
        self.assertEqual(
            provider._resolve_model("deepseek/deepseek-v4-flash"),
            "deepseek/deepseek-v4-flash",
        )

    @patch("providers.anyllm_chat.ProviderFactory.get_supported_providers")
    def test_model_with_unsupported_provider_prefix_raises(self, mock_supported) -> None:
        mock_supported.return_value = ["deepseek", "openai"]
        provider = AnyLLMChatProvider(
            ProviderConfig(provider_name="deepseek", api_key="sk-test", default_model="deepseek-v4-pro")
        )
        with self.assertRaises(RuntimeError):
            provider._resolve_model("dashscope/qwen3.7-max")

    @patch("providers.anyllm_chat.ProviderFactory.get_supported_providers")
    def test_missing_default_model_raises(self, mock_supported) -> None:
        mock_supported.return_value = ["deepseek", "openai"]
        provider = AnyLLMChatProvider(
            ProviderConfig(provider_name="deepseek", api_key="sk-test", default_model="")
        )
        with self.assertRaises(ValueError):
            provider._resolve_model(None)


if __name__ == "__main__":
    unittest.main(verbosity=2)
