"""视频生成 Provider 抽象基类。"""

from abc import ABC, abstractmethod
from typing import Any, Callable

from models.data_models import ModelInfo, ProviderConfig, TaskResult


class VideoProvider(ABC):
    """所有视频生成厂商的统一接口。"""

    def __init__(self, config: ProviderConfig) -> None:
        self._config = config

    @property
    def provider_name(self) -> str:
        return self._config.provider_name

    @abstractmethod
    def submit(self, prompt: str, params: dict[str, Any] | None = None) -> tuple[str, dict[str, Any]]:
        """提交生成任务，返回 (task_id, 完整请求参数)。"""

    @abstractmethod
    def check_status(self, task_id: str) -> TaskResult:
        """查询任务状态。"""

    @abstractmethod
    def download(
        self,
        video_url: str,
        save_path: str,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> str:
        """下载视频到本地，返回最终文件路径。progress_callback(downloaded, total)。"""

    @abstractmethod
    def get_model_info(self) -> list[ModelInfo]:
        """返回当前 Provider 支持的模型列表。"""
