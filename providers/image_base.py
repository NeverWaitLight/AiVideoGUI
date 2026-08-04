from abc import ABC, abstractmethod
from typing import Any

from models.provider_config import ProviderConfig


class ImageProvider(ABC):

    def __init__(self, config: ProviderConfig) -> None:
        self._config = config

    @property
    def provider_name(self) -> str:
        return self._config.provider_name

    @property
    @abstractmethod
    def submit_url(self) -> str:
        """API 提交地址"""
        pass

    @abstractmethod
    def build_headers(self) -> dict[str, str]:
        """构建请求头"""
        pass

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
    ) -> tuple[str, dict[str, Any]]:
        """生成图片，返回 (image_url, request_payload)"""
        pass

    @abstractmethod
    def download(self, image_url: str, save_path: str) -> str:
        pass

    @abstractmethod
    def list_available_models(self) -> list[str]:
        """获取该 provider 支持的所有图片模型列表"""
        pass
