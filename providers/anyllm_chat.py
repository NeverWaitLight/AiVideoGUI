from loguru import logger

import any_llm
from any_llm.provider import ProviderFactory

from config.url_resolver import get_chat_base_url
from models.provider_config import ProviderConfig
from providers.chat_base import ChatProvider

_DEFAULT_TIMEOUT = 1800.0

_PROVIDER_ALIASES: dict[str, str] = {
    "dashscope": "openai",
    "bailian": "openai",
    "deepseek": "openai",
    "openai": "openai",
}

class AnyLLMChatProvider(ChatProvider):
    """基于 any-llm-sdk 的统一文本模型 ChatProvider 实现"""

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        self._api_base = get_chat_base_url(config)

    def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        **kwargs,
    ) -> str:
        resolved_model = self._resolve_model(model)
        params = {**self._config.default_params, **kwargs}

        logger.info(f"调用文本模型：provider={self.provider_name}, model={resolved_model}")

        try:
            completion_kwargs: dict = {
                "model": resolved_model,
                "messages": messages,
                "api_key": self._config.api_key,
                "api_timeout": _DEFAULT_TIMEOUT,
                **params,
            }
            if self._api_base:
                completion_kwargs["api_base"] = self._api_base

            response = any_llm.completion(**completion_kwargs)
            content = response.choices[0].message.content or ""
            return content.strip()
        except Exception as e:
            logger.exception(f"文本模型调用失败：{e}")
            raise RuntimeError(f"文本模型调用失败：{e}") from e

    def _resolve_model(self, model: str | None = None) -> str:
        model_name = model or self._config.default_model
        if not model_name:
            raise ValueError("未配置默认模型")
        if "/" in model_name:
            return model_name

        provider_key = _PROVIDER_ALIASES.get(
            self._config.provider_name,
            self._config.provider_name,
        )
        supported = ProviderFactory.get_supported_providers()
        if provider_key not in supported:
            logger.warning(
                f"供应商 {provider_key} 不在 any-llm 支持列表中，回退到 openai"
            )
            provider_key = "openai"
        return f"{provider_key}/{model_name}"
