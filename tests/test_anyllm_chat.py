import unittest
from types import SimpleNamespace
from unittest.mock import patch

from models.provider_config import ProviderConfig
from providers.anyllm_chat import (
    AnyLLMChatProvider,
    _require_supported_provider,
)
from providers.chat_base import ChatProvider


def _make_stream_chunk(content: str):
    return SimpleNamespace(
        choices=[SimpleNamespace(delta=SimpleNamespace(content=content))]
    )


def _make_full_response(content: str):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
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

    @patch("providers.anyllm_chat.any_llm.completion")
    @patch("providers.anyllm_chat.ProviderFactory.get_supported_providers")
    def test_chat_stream_emits_chunks_and_returns_full_content(
        self, mock_supported, mock_completion
    ) -> None:
        mock_supported.return_value = ["deepseek", "openai"]
        mock_completion.return_value = iter(
            [
                _make_stream_chunk("你好"),
                _make_stream_chunk("，"),
                _make_stream_chunk("世界"),
                _make_stream_chunk(None),
            ]
        )
        provider = AnyLLMChatProvider(
            ProviderConfig(provider_name="deepseek", api_key="sk-test", default_model="deepseek-v4-pro")
        )

        chunks: list[str] = []
        content, task_id = provider.chat_stream(
            messages=[{"role": "user", "content": "hi"}],
            on_chunk=chunks.append,
        )

        self.assertEqual(content, "你好，世界")
        self.assertEqual(chunks, ["你好", "，", "世界"])
        self.assertIsNone(task_id)
        mock_completion.assert_called_once()
        call_kwargs = mock_completion.call_args.kwargs
        self.assertTrue(call_kwargs.get("stream"))

    @patch("providers.anyllm_chat.any_llm.completion")
    @patch("providers.anyllm_chat.ProviderFactory.get_supported_providers")
    def test_chat_stream_strips_final_content(self, mock_supported, mock_completion) -> None:
        mock_supported.return_value = ["deepseek", "openai"]
        mock_completion.return_value = iter([_make_stream_chunk("  hello  ")])
        provider = AnyLLMChatProvider(
            ProviderConfig(provider_name="deepseek", api_key="sk-test", default_model="deepseek-v4-pro")
        )

        content, _ = provider.chat_stream(messages=[{"role": "user", "content": "hi"}])

        self.assertEqual(content, "hello")

    @patch("providers.anyllm_chat.any_llm.completion")
    @patch("providers.anyllm_chat.ProviderFactory.get_supported_providers")
    def test_chat_returns_full_content_without_stream(
        self, mock_supported, mock_completion
    ) -> None:
        mock_supported.return_value = ["deepseek", "openai"]
        mock_completion.return_value = _make_full_response("  full response  ")
        provider = AnyLLMChatProvider(
            ProviderConfig(provider_name="deepseek", api_key="sk-test", default_model="deepseek-v4-pro")
        )

        content, task_id = provider.chat(messages=[{"role": "user", "content": "hi"}])

        self.assertEqual(content, "full response")
        self.assertIsNone(task_id)
        mock_completion.assert_called_once()
        call_kwargs = mock_completion.call_args.kwargs
        self.assertNotIn("stream", call_kwargs)

    @patch("providers.anyllm_chat.any_llm.completion")
    @patch("providers.anyllm_chat.ProviderFactory.get_supported_providers")
    def test_chat_provider_implements_both_methods(
        self, mock_supported, mock_completion
    ) -> None:
        mock_supported.return_value = ["deepseek", "openai"]
        mock_completion.return_value = _make_full_response("sync")
        provider = AnyLLMChatProvider(
            ProviderConfig(provider_name="deepseek", api_key="sk-test", default_model="deepseek-v4-pro")
        )

        self.assertIsInstance(provider, ChatProvider)
        sync_content, _ = provider.chat(messages=[{"role": "user", "content": "hi"}])
        self.assertEqual(sync_content, "sync")

        mock_completion.return_value = iter([_make_stream_chunk("stream")])
        stream_content, _ = provider.chat_stream(
            messages=[{"role": "user", "content": "hi"}],
            on_chunk=lambda _: None,
        )
        self.assertEqual(stream_content, "stream")


if __name__ == "__main__":
    unittest.main(verbosity=2)
