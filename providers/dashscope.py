"""阿里万象 DashScope 视频生成 Provider。"""

import logging
import os
from typing import Any, Callable

import requests

from models.data_models import ModelInfo, ProviderConfig, TaskResult, TaskStatus
from providers.base import VideoProvider

logger = logging.getLogger(__name__)


class DashScopeProvider(VideoProvider):
    """阿里万象 DashScope 视频生成实现。"""

    BASE_URL = "https://dashscope.aliyuncs.com/api/v1"
    SUBMIT_URL = f"{BASE_URL}/services/aigc/video-generation/video-synthesis"
    TASK_URL = f"{BASE_URL}/tasks"
    DEFAULT_MODEL = "wan2.7-t2v"

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        self._api_key = config.api_key
        self._base_url = config.base_url or self.BASE_URL
        self._model = config.default_model or self.DEFAULT_MODEL

    def _headers(self, *, async_mode: bool = False) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        if async_mode:
            headers["X-DashScope-Async"] = "enable"
        return headers

    def submit(self, prompt: str, params: dict[str, Any] | None = None) -> str:
        """提交文生视频任务，返回 task_id。"""
        payload = {
            "model": self._model,
            "input": {"prompt": prompt},
            "parameters": params or {},
        }
        logger.info("提交 DashScope 任务，模型：%s", self._model)
        logger.debug("请求体：%s", payload)

        resp = requests.post(
            self.SUBMIT_URL,
            json=payload,
            headers=self._headers(async_mode=True),
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        logger.debug("提交响应：%s", data)

        output = data.get("output", {})
        task_id = output.get("task_id", "")
        if not task_id:
            raise RuntimeError(f"DashScope 未返回 task_id: {data}")
        logger.info("任务已提交，task_id=%s", task_id)
        return task_id

    def check_status(self, task_id: str) -> TaskResult:
        """查询任务状态。"""
        url = f"{self.TASK_URL}/{task_id}"
        resp = requests.get(url, headers=self._headers(), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        logger.debug("状态查询响应：%s", data)

        output = data.get("output", {})
        task_status = output.get("task_status", "")

        if task_status == "SUCCEEDED":
            results = output.get("results", [])
            video_url = ""
            if results and isinstance(results, list):
                video_url = results[0].get("url", "")
            elif isinstance(results, dict):
                video_url = results.get("url", "")
            logger.info("任务成功，video_url=%s", video_url)
            return TaskResult(status=TaskStatus.SUCCEEDED, video_url=video_url)

        if task_status == "FAILED":
            message = output.get("message", "未知错误")
            logger.error("任务失败：%s", message)
            return TaskResult(status=TaskStatus.FAILED, error_message=message)

        if task_status == "RUNNING":
            return TaskResult(status=TaskStatus.RUNNING)

        return TaskResult(status=TaskStatus.PENDING)

    def download(
        self,
        video_url: str,
        save_path: str,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> str:
        """流式下载视频到本地。"""
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        logger.info("开始下载视频：%s -> %s", video_url, save_path)

        with requests.get(video_url, stream=True, timeout=60) as resp:
            resp.raise_for_status()
            total = int(resp.headers.get("content-length", 0))
            downloaded = 0
            with open(save_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback:
                        progress_callback(downloaded, total)

        logger.info("下载完成：%s", save_path)
        return save_path

    def get_model_info(self) -> list[ModelInfo]:
        """返回支持的模型列表。"""
        return [
            ModelInfo(
                name=self._model,
                provider_name=self.provider_name,
                supported_resolutions=["480P", "720P", "1080P"],
                supported_ratios=["16:9", "9:16", "1:1"],
                max_duration=15,
                description="阿里万象 wan2.7 文生视频模型",
            ),
        ]
