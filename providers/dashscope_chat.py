from loguru import logger

import requests

from models.provider_config import ProviderConfig
from providers.chat_base import ChatProvider

_DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

class DashScopeChatProvider(ChatProvider):

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        self._base_url = (
            config.base_url.rstrip("/") if config.base_url else _DEFAULT_BASE_URL
        )

    def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        **kwargs,
    ) -> str:
        url = f"{self._base_url}/chat/completions"
        payload = {
            "model": model or self._config.default_model or "qwen-turbo",
            "messages": messages,
            **kwargs,
        }
        resp = requests.post(url, json=payload, headers=self._headers(), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    def list_available_models(self) -> list[str]:
        url = f"{self._base_url}/models"
        resp = requests.get(url, headers=self._headers(), timeout=15)
        resp.raise_for_status()
        data = resp.json()
        models = [item["id"] for item in data.get("data", [])]
        models.sort()
        return models

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._config.api_key}",
            "Content-Type": "application/json",
        }
