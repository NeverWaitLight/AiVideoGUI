"""Seedance 视频生成 Provider。"""

import logging
import os
from typing import Any, Callable

import requests

from models.data_models import ModelInfo, ProviderConfig, TaskResult, TaskStatus
from providers.video_base import VideoProvider

logger = logging.getLogger(__name__)


class SeedanceVideoProvider(VideoProvider):
    """Seedance 视频生成实现（支持 Seedance 2.0 和 2.5）。"""

    BASE_URL = "https://api.evolink.ai/v1"
    SUBMIT_URL = f"{BASE_URL}/videos/generations"
    TASK_URL = f"{BASE_URL}/tasks"
    DEFAULT_MODEL = "seedance-2.0-text-to-video"

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        self._api_key = config.api_key
        self._base_url = config.base_url or self.BASE_URL
        self._model = config.default_model or self.DEFAULT_MODEL

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    def build_payload(self, prompt: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """构建提交给 Seedance API 的完整请求体（不发起网络请求）。

        支持的参数：
        - duration: 视频时长 (4-15秒)，默认 5
        - quality: 画质 ("480p" | "720p" | "1080p" | "4k")，默认 "720p"
        - aspect_ratio: 宽高比 ("16:9" | "9:16" | "1:1" | "4:3" | "3:4" | "21:9" | "adaptive")，默认 "16:9"
        - generate_audio: 是否生成同步音频 (bool)，默认 True
        - model_params.web_search: 是否启用联网检索 (bool)，默认 False
        - callback_url: 任务完成回调 URL (str)，可选
        """
        api_params = params.copy() if params else {}

        # 基础参数
        payload = {
            "model": self._model,
            "prompt": prompt,
            "duration": api_params.pop("duration", 5),
            "quality": api_params.pop("quality", "720p"),
            "aspect_ratio": api_params.pop("aspect_ratio", "16:9"),
            "generate_audio": api_params.pop("generate_audio", True),
        }

        # 可选的高级参数
        if "callback_url" in api_params:
            payload["callback_url"] = api_params.pop("callback_url")

        # model_params 嵌套参数
        model_params = {}
        if "web_search" in api_params:
            model_params["web_search"] = api_params.pop("web_search")

        if model_params:
            payload["model_params"] = model_params

        return payload

    def submit(self, prompt: str, params: dict[str, Any] | None = None) -> tuple[str, dict[str, Any]]:
        """提交文生视频任务，返回 (task_id, 完整请求参数)。"""
        payload = self.build_payload(prompt, params)
        logger.info("提交 Seedance 任务，模型：%s", self._model)
        logger.debug("请求体：%s", payload)

        resp = requests.post(
            self.SUBMIT_URL,
            json=payload,
            headers=self._headers(),
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        logger.debug("提交响应：%s", data)

        task_id = data.get("id", "")
        if not task_id:
            raise RuntimeError(f"Seedance 未返回 task_id: {data}")
        logger.info("任务已提交，task_id=%s", task_id)
        return task_id, payload

    def check_status(self, task_id: str) -> TaskResult:
        """查询任务状态。"""
        url = f"{self.TASK_URL}/{task_id}"
        resp = requests.get(url, headers=self._headers(), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        logger.debug("状态查询响应：%s", data)

        status = data.get("status", "")

        if status == "completed":
            video_url = data.get("video_url", "")
            if not video_url:
                raise RuntimeError(f"任务已完成但未返回 video_url: {data}")
            logger.info("任务成功，video_url=%s", video_url)
            return TaskResult(status=TaskStatus.SUCCEEDED, video_url=video_url)

        if status == "failed":
            error_message = data.get("error", {}).get("message", "未知错误")
            logger.error("任务失败：%s", error_message)
            return TaskResult(status=TaskStatus.FAILED, error_message=error_message)

        if status == "processing":
            return TaskResult(status=TaskStatus.RUNNING)

        # pending 或其他未知状态
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
        # 根据当前模型返回对应的能力信息
        if "2.5" in self._model or "seedance-2.5" in self._model:
            # Seedance 2.5（原生 4K，30 秒，50 个参考）
            return [
                ModelInfo(
                    name=self._model,
                    provider_name=self.provider_name,
                    supported_resolutions=["480p", "720p", "1080p", "4k"],
                    supported_ratios=["16:9", "9:16", "1:1", "4:3", "3:4", "21:9", "adaptive"],
                    max_duration=30,  # 2.5 支持 30 秒
                    description="Seedance 2.5 文生视频模型（原生 4K，最长 30 秒）",
                ),
            ]
        else:
            # Seedance 2.0（默认）
            return [
                ModelInfo(
                    name=self._model,
                    provider_name=self.provider_name,
                    supported_resolutions=["480p", "720p", "1080p", "4k"],
                    supported_ratios=["16:9", "9:16", "1:1", "4:3", "3:4", "21:9", "adaptive"],
                    max_duration=15,  # 2.0 支持 4-15 秒
                    description="Seedance 2.0 文生视频模型（最长 15 秒）",
                ),
            ]
