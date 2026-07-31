from abc import ABC, abstractmethod

from models.provider_config import ProviderConfig


class ImageProvider(ABC):

    def __init__(self, config: ProviderConfig) -> None:
        self._config = config

    @property
    def provider_name(self) -> str:
        return self._config.provider_name

    @abstractmethod
    def generate(
        self,
        prompt: str,
        size: str = "1280*1280",
        negative_prompt: str = "",
        n: int = 1,
        prompt_extend: bool = True,
        watermark: bool = False,
        seed: int | None = None,
    ) -> str:
        pass

    @abstractmethod
    def download(self, image_url: str, save_path: str) -> str:
        pass
