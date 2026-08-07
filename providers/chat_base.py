from abc import ABC, abstractmethod

from models.provider_config import ProviderConfig


class ChatProvider(ABC):

    def __init__(self, config: ProviderConfig) -> None:
        self._config = config

    @property
    def provider_name(self) -> str:
        return self._config.provider_name

    @abstractmethod
    def chat(self, messages: list[dict[str, str]]) -> str:
        pass

    @abstractmethod
    def list_available_models(self) -> list[str]:
        pass
