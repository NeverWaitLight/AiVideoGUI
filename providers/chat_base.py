from abc import ABC, abstractmethod
from collections.abc import Callable

from models.generate_task_context import GenerateTaskContext
from models.provider_config import ProviderConfig


class ChatProvider(ABC):

    def __init__(self, config: ProviderConfig) -> None:
        self._config = config

    @property
    def provider_name(self) -> str:
        return self._config.provider_name

    @abstractmethod
    def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        task_context: GenerateTaskContext | None = None,
        **kwargs,
    ) -> tuple[str, int | None]:
        pass

    @abstractmethod
    def chat_stream(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        task_context: GenerateTaskContext | None = None,
        on_chunk: Callable[[str], None] | None = None,
        **kwargs,
    ) -> tuple[str, int | None]:
        pass
