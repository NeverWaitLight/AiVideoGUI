"""图片生成 Provider 抽象基类。"""

from abc import ABC, abstractmethod

from models.data_models import ProviderConfig


class ImageProvider(ABC):
    """所有图片生成厂商的统一接口。"""

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
        """同步生成图片，返回图片 URL。"""

    @abstractmethod
    def download(self, image_url: str, save_path: str) -> str:
        """下载图片到本地，返回最终文件路径。"""
