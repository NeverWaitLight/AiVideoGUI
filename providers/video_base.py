"""视频生成 Provider 抽象基类。"""

from abc import ABC, abstractmethod
from typing import Any, Callable

from models.model_info import ModelInfo
from models.provider_config import ProviderConfig
from models.task_result import TaskResult


class VideoProvider(ABC):
    """所有视频生成厂商的统一接口。"""

    def __init__(self, config: ProviderConfig) -> None:
        self._config = config

    @property
    def provider_name(self) -> str:
        return self._config.provider_name

    @abstractmethod
    def build_payload(self, prompt: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """构建提交给 API 的完整请求体（不发起网络请求）。"""

    @abstractmethod
    def t2v(self, prompt: str, params: dict[str, Any] | None = None) -> tuple[str, dict[str, Any]]:
        """文生视频：提交文本生成视频任务，返回 (task_id, 完整请求参数)。"""

    @abstractmethod
    def p2v(
        self, prompt: str, image_path: str, params: dict[str, Any] | None = None
    ) -> tuple[str, dict[str, Any]]:
        """图生视频：提交图片+文本生成视频任务，返回 (task_id, 完整请求参数)。"""

    @abstractmethod
    def r2v(
        self, prompt: str, reference_path: str, params: dict[str, Any] | None = None
    ) -> tuple[str, dict[str, Any]]:
        """参考生视频：提交参考素材+文本生成视频任务，返回 (task_id, 完整请求参数)。"""

    @abstractmethod
    def extend(
        self, prompt: str, video_path: str, params: dict[str, Any] | None = None
    ) -> tuple[str, dict[str, Any]]:
        """视频续写：基于已有视频继续生成后续内容，返回 (task_id, 完整请求参数)。"""

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
