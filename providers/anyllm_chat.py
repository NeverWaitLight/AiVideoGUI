from loguru import logger

import any_llm
from any_llm.provider import ProviderFactory

from config.url_resolver import get_chat_base_url
from models.provider_config import ProviderConfig
from providers.chat_base import ChatProvider

_DEFAULT_TIMEOUT = 1800.0


def _catalog_provider_id(provider_name: str) -> str:
    if provider_name.endswith("_chat"):
        return provider_name[:-5]
    return provider_name


def _supported_providers() -> set[str]:
    return set(ProviderFactory.get_supported_providers())


def _require_supported_provider(provider_id: str) -> str:
    supported = _supported_providers()
    if provider_id not in supported:
        supported_text = ", ".join(sorted(supported))
        raise RuntimeError(
            f"供应商 {provider_id} 不在 any-llm 支持列表中。当前支持：{supported_text}"
        )
    return provider_id


class AnyLLMChatProvider(ChatProvider):
    """基于 any-llm-sdk 的统一文本模型 ChatProvider 实现"""

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        self._api_base = get_chat_base_url(config)
        self._anyllm_provider_key = _require_supported_provider(
            _catalog_provider_id(config.provider_name)
        )

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
            provider_id, model_id = model_name.split("/", 1)
            if not provider_id.strip():
                raise ValueError(f"模型格式无效：{model_name}")
            if not model_id.strip():
                raise ValueError(f"未指定模型名称：{model_name}")
            _require_supported_provider(provider_id.strip())
            return f"{provider_id.strip()}/{model_id.strip()}"

        return f"{self._anyllm_provider_key}/{model_name}"
