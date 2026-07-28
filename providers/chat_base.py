"""对话模型 Provider 抽象基类。"""

from abc import ABC, abstractmethod

from models.provider_config import ProviderConfig


class ChatProvider(ABC):
    """所有对话模型厂商的统一接口。"""

    def __init__(self, config: ProviderConfig) -> None:
        self._config = config

    @property
    def provider_name(self) -> str:
        return self._config.provider_name

    @abstractmethod
    def chat(self, messages: list[dict[str, str]]) -> str:
        """发送对话消息，返回助手回复文本。"""

    @abstractmethod
    def list_available_models(self) -> list[str]:
        """查询当前账号可用的模型 ID 列表。"""
