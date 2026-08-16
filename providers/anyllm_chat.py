from loguru import logger

import requests

import any_llm
from any_llm.provider import ProviderFactory

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
        self._api_base = self._resolve_api_base()

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

    def list_available_models(self) -> list[str]:
        if not self._api_base:
            return []
        url = f"{self._api_base.rstrip('/')}/models"
        try:
            resp = requests.get(url, headers=self._headers(), timeout=15)
            resp.raise_for_status()
            data = resp.json()
            models = [item["id"] for item in data.get("data", [])]
            models.sort()
            return models
        except Exception as e:
            logger.warning(f"获取模型列表失败：{e}")
            return []

    def _resolve_api_base(self) -> str:
        if self._config.base_url:
            return self._config.base_url.rstrip("/")
        return ""

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

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._config.api_key}",
            "Content-Type": "application/json",
        }
