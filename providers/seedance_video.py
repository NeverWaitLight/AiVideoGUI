from loguru import logger
import os
from typing import Any, Callable

import requests

from models.enums import TaskStatus
from models.model_info import ModelInfo
from models.provider_config import ProviderConfig
from models.task_result import TaskResult
from providers.video_base import VideoProvider

class SeedanceVideoProvider(VideoProvider):

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
        api_params = params.copy() if params else {}

        payload = {
            "model": self._model,
            "prompt": prompt,
            "duration": api_params.pop("duration", 5),
            "quality": api_params.pop("quality", "720p"),
            "aspect_ratio": api_params.pop("aspect_ratio", "16:9"),
            "generate_audio": api_params.pop("generate_audio", True),
        }

        if "callback_url" in api_params:
            payload["callback_url"] = api_params.pop("callback_url")

        model_params = {}
        if "web_search" in api_params:
            model_params["web_search"] = api_params.pop("web_search")

        if model_params:
            payload["model_params"] = model_params

        return payload

    def _submit_task(self, payload: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        logger.info(f"提交 Seedance 任务，模型：{self._model}")
        logger.debug(f"请求体：{payload}")

        headers = self._headers()

        resp = requests.post(
            self.SUBMIT_URL,
            json=payload,
            headers=headers,
            timeout=30,
        )

        if not resp.ok:
            try:
                error_data = resp.json()
                error_detail = error_data.get("error", {}).get("message", "") or error_data.get("message", "") or resp.text
            except Exception:
                error_detail = resp.text
            logger.error(f"Seedance API 返回 {resp.status_code}: {error_detail}")
            raise RuntimeError(f"Seedance API 错误 ({resp.status_code}): {error_detail}")

        data = resp.json()
        logger.debug(f"提交响应：{data}")

        task_id = data.get("id", "")
        if not task_id:
            raise RuntimeError(f"Seedance 未返回 task_id: {data}")
        logger.info(f"任务已提交，task_id={task_id}")
        return task_id, {"url": self.SUBMIT_URL, "json": payload, "headers": headers}

    def t2v(self, prompt: str, params: dict[str, Any] | None = None) -> tuple[str, dict[str, Any]]:
        payload = self.build_payload(prompt, params)
        return self._submit_task(payload)

    def p2v(
        self, prompt: str, image_path: str, params: dict[str, Any] | None = None
    ) -> tuple[str, dict[str, Any]]:
        raise NotImplementedError("Seedance p2v 尚未实现")

    def r2v(
        self, prompt: str, reference_path: str, params: dict[str, Any] | None = None
    ) -> tuple[str, dict[str, Any]]:
        raise NotImplementedError("Seedance r2v 尚未实现")

    def extend(
        self, prompt: str, video_path: str, params: dict[str, Any] | None = None
    ) -> tuple[str, dict[str, Any]]:
        raise NotImplementedError("Seedance extend 尚未实现")

    def check_status(self, task_id: str) -> TaskResult:
        url = f"{self.TASK_URL}/{task_id}"
        resp = requests.get(url, headers=self._headers(), timeout=30)

        if not resp.ok:
            try:
                error_data = resp.json()
                error_detail = error_data.get("error", {}).get("message", "") or error_data.get("message", "") or resp.text
            except Exception:
                error_detail = resp.text
            logger.error(f"Seedance 状态查询失败 ({resp.status_code}): {error_detail}")
            raise RuntimeError(f"Seedance 状态查询错误 ({resp.status_code}): {error_detail}")

        data = resp.json()
        logger.debug(f"状态查询响应：{data}")

        status = data.get("status", "")

        if status == "completed":
            video_url = data.get("video_url", "")
            if not video_url:
                raise RuntimeError(f"任务已完成但未返回 video_url: {data}")
            logger.info(f"任务成功，video_url={video_url}")
            return TaskResult(status=TaskStatus.SUCCEEDED, video_url=video_url)

        if status == "failed":
            error_message = data.get("error", {}).get("message", "未知错误")
            logger.error(f"任务失败：{error_message}")
            return TaskResult(status=TaskStatus.FAILED, error_message=error_message)

        if status == "processing":
            return TaskResult(status=TaskStatus.RUNNING)

        return TaskResult(status=TaskStatus.PENDING)

    def download(
        self,
        video_url: str,
        save_path: str,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> str:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        logger.info(f"开始下载视频：{video_url} -> {save_path}")

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

        logger.info(f"下载完成：{save_path}")
        return save_path

    def get_model_info(self) -> list[ModelInfo]:
        if "2.5" in self._model or "seedance-2.5" in self._model:
            return [
                ModelInfo(
                    name=self._model,
                    provider_name=self.provider_name,
                    supported_resolutions=["480p", "720p", "1080p", "4k"],
                    supported_ratios=["16:9", "9:16", "1:1", "4:3", "3:4", "21:9", "adaptive"],
                    max_duration=30,
                    description="Seedance 2.5 文生视频模型（原生 4K，最长 30 秒）",
                ),
            ]
        else:
            return [
                ModelInfo(
                    name=self._model,
                    provider_name=self.provider_name,
                    supported_resolutions=["480p", "720p", "1080p", "4k"],
                    supported_ratios=["16:9", "9:16", "1:1", "4:3", "3:4", "21:9", "adaptive"],
                    max_duration=15,
                    description="Seedance 2.0 文生视频模型（最长 15 秒）",
                ),
            ]
