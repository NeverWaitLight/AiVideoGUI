from abc import ABC, abstractmethod
from typing import Any, Callable

from models.model_info import ModelInfo
from models.provider_config import ProviderConfig
from models.task_result import TaskResult


class VideoProvider(ABC):

    def __init__(self, config: ProviderConfig) -> None:
        self._config = config

    @property
    def provider_name(self) -> str:
        return self._config.provider_name

    @abstractmethod
    def build_payload(self, prompt: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        pass

    @abstractmethod
    def t2v(self, prompt: str, params: dict[str, Any] | None = None) -> tuple[str, dict[str, Any]]:
        """文生视频，返回 (task_id, request_details)，其中 request_details 包含 url/json/headers"""
        pass

    @abstractmethod
    def p2v(
        self, prompt: str, image_path: str, params: dict[str, Any] | None = None
    ) -> tuple[str, dict[str, Any]]:
        """图生视频，返回 (task_id, request_details)"""
        pass

    @abstractmethod
    def r2v(
        self, prompt: str, reference_path: str, params: dict[str, Any] | None = None
    ) -> tuple[str, dict[str, Any]]:
        """参考生视频，返回 (task_id, request_details)"""
        pass

    @abstractmethod
    def extend(
        self, prompt: str, video_path: str, params: dict[str, Any] | None = None
    ) -> tuple[str, dict[str, Any]]:
        """视频续写，返回 (task_id, request_details)"""
        pass

    @abstractmethod
    def check_status(self, task_id: str) -> TaskResult:
        pass

    @abstractmethod
    def download(
        self,
        video_url: str,
        save_path: str,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> str:
        pass

    @abstractmethod
    def get_model_info(self) -> list[ModelInfo]:
        pass
