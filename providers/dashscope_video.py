from loguru import logger
import os
import re
from pathlib import Path
from typing import Any, Callable

import requests

from models.api_params import DashScopeVideoRequest, MediaItem
from models.enums import TaskStatus
from models.exceptions import MissingConfigError
from models.model_info import ModelInfo
from models.provider_config import ProviderConfig
from models.task_result import TaskResult
from providers.dashscope_oss_uploader import DashScopeOSSUploader
from providers.video_base import VideoProvider
from storage.repositories.oss_cache_repository import OSSFileCacheRepository
from storage.session_manager import SessionManager

class DashScopeVideoProvider(VideoProvider):

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)

        # 验证必需配置
        missing_fields = []
        if not config.api_key:
            missing_fields.append("api_key")
        if not config.base_url:
            missing_fields.append("base_url")

        # DashScope 使用 model_mappings 为不同任务类型配置模型
        # 不强制要求 default_model，但至少需要配置一个任务类型的模型
        self._model_mappings = config.model_mappings or {}
        if not self._model_mappings and not config.default_model:
            missing_fields.append("model_mappings 或 default_model")

        if missing_fields:
            hint = "DashScope 视频生成服务需要配置 API Key、Base URL 和模型映射。\n"
            hint += "建议在 model_mappings 中配置：\n"
            hint += '  {"t2v": "wan2.7-t2v-2026-06-12", "i2v": "wan2.7-i2v-2026-04-25", "r2v": "wan2.7-r2v-2026-06-12"}\n'
            hint += "或至少配置一个 default_model 作为后备"
            raise MissingConfigError(
                provider_name=config.provider_name or "dashscope",
                missing_fields=missing_fields,
                config_hint=hint
            )

        self._api_key = config.api_key
        self._base_url = config.base_url
        self._model = config.default_model or ""

        # 实例级别 URL 拼接
        self._submit_url = f"{self._base_url}/api/v1/services/aigc/video-generation/video-synthesis"
        self._task_url = f"{self._base_url}/api/v1/tasks"

        self._oss_uploader = DashScopeOSSUploader(self._api_key, base_url=self._base_url)
        self._session_manager = None

    def set_session_manager(self, session_manager: SessionManager) -> None:
        self._session_manager = session_manager

    @staticmethod
    def _is_local_file(path: str) -> bool:
        if not path:
            return False
        if path.startswith(("http://", "https://", "oss://")):
            return False
        return Path(path).exists()

    def _upload_file_if_needed(self, file_path: str) -> str:
        if not file_path:
            return file_path

        if not file_path.startswith(("http://", "https://", "oss://")) and not Path(file_path).exists():
            raise RuntimeError(f"本地文件不存在：{file_path}")

        if not self._is_local_file(file_path):
            return file_path

        logger.debug(f"检测到本地文件: {file_path}")

        if self._session_manager:
            oss_cache_repo = self._session_manager.get_repo(OSSFileCacheRepository)
            cache = oss_cache_repo.get_valid_cache(file_path=file_path, model_name=self._model)
            if cache:
                logger.info(f"命中 OSS 缓存: {file_path} -> {cache.oss_url}")
                return cache.oss_url

        logger.info(f"上传文件到 OSS: {file_path}")
        oss_url, expire_time = self._oss_uploader.upload(file_path=file_path, model_name=self._model)

        if self._session_manager:
            try:
                self._session_manager.begin_write()
                oss_cache_repo = self._session_manager.get_repo(OSSFileCacheRepository)
                oss_cache_repo.save_cache(file_path=file_path, model_name=self._model, oss_url=oss_url)
                self._session_manager.commit_write()
            except Exception as e:
                self._session_manager.rollback_write()
                logger.warning(f"保存 OSS 缓存失败（不影响任务提交）: {e}")

        return oss_url

    def _headers(self, *, async_mode: bool = False) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        if async_mode:
            headers["X-DashScope-Async"] = "enable"
        headers["X-DashScope-OssResourceResolve"] = "enable"
        return headers

    def build_payload(self, prompt: str, params: dict[str, Any] | None = None, model: str | None = None) -> dict[str, Any]:
        api_params = params.copy() if params else {}

        input_obj = {"prompt": prompt}

        if "negative_prompt" in api_params:
            input_obj["negative_prompt"] = api_params.pop("negative_prompt")

        if "audio_url" in api_params:
            input_obj["audio_url"] = api_params.pop("audio_url")

        return {
            "model": model or self._model,
            "input": input_obj,
            "parameters": api_params,
        }

    def _submit_task(self, payload: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        logger.info(f"提交 DashScope 任务，模型：{self._model}")
        logger.debug(f"请求体：{payload}")

        headers = self._headers(async_mode=True)

        resp = requests.post(
            self._submit_url,
            json=payload,
            headers=headers,
            timeout=30,
        )

        if not resp.ok:
            try:
                error_data = resp.json()
                code = error_data.get("code", "")
                message = error_data.get("message", "")
                error_detail = f"[{code}] {message}" if code else (message or resp.text)
            except Exception:
                error_detail = resp.text
            logger.error(f"DashScope API 返回 {resp.status_code}: {error_detail}")
            raise RuntimeError(f"DashScope API 错误 ({resp.status_code}): {error_detail}")

        data = resp.json()
        logger.debug(f"提交响应：{data}")

        output = data.get("output", {})
        task_id = output.get("task_id", "")
        if not task_id:
            raise RuntimeError(f"DashScope 未返回 task_id: {data}")
        logger.info(f"任务已提交，task_id={task_id}")
        return task_id, {"url": self._submit_url, "json": payload, "headers": headers}

    def t2v(self, prompt: str, params: dict[str, Any] | None = None) -> tuple[str, dict[str, Any]]:
        api_params = params.copy() if params else {}

        negative_prompt = api_params.pop("negative_prompt", None)
        audio_url = api_params.pop("audio_url", None)
        resolution = api_params.pop("resolution", None)
        ratio = api_params.pop("ratio", None)
        duration = api_params.pop("duration", None)
        prompt_extend = api_params.pop("prompt_extend", True)
        watermark = api_params.pop("watermark", False)

        model = self._model_mappings.get("t2v") or self._model_mappings.get("default") or self._model
        request = DashScopeVideoRequest.for_t2v(
            model=model,
            prompt=prompt,
            negative_prompt=negative_prompt,
            audio_url=audio_url,
            resolution=resolution,
            ratio=ratio,
            duration=duration,
            prompt_extend=prompt_extend,
            watermark=watermark,
            **api_params,
        )

        payload = request.to_dict()
        return self._submit_task(payload=payload)

    def p2v(
        self, prompt: str, image_path: str, params: dict[str, Any] | None = None
    ) -> tuple[str, dict[str, Any]]:
        api_params = params.copy() if params else {}
        last_frame_path = api_params.pop("last_frame_path", None)
        driving_audio_path = api_params.pop("driving_audio_path", None)

        image_path = self._upload_file_if_needed(image_path)
        if last_frame_path:
            last_frame_path = self._upload_file_if_needed(last_frame_path)
        if driving_audio_path:
            driving_audio_path = self._upload_file_if_needed(driving_audio_path)

        media: list[MediaItem] = [MediaItem(type="first_frame", url=image_path)]

        if last_frame_path:
            media.append(MediaItem(type="last_frame", url=last_frame_path))

        if driving_audio_path:
            media.append(MediaItem(type="driving_audio", url=driving_audio_path))

        model = self._model_mappings.get("i2v") or self._model_mappings.get("default") or self._model
        request = DashScopeVideoRequest.for_r2v(
            model=model,
            prompt=prompt,
            media=media,
            negative_prompt=api_params.pop("negative_prompt", None),
            resolution=api_params.pop("resolution", None),
            ratio=api_params.pop("ratio", None),
            duration=api_params.pop("duration", None),
            prompt_extend=api_params.pop("prompt_extend", True),
            watermark=api_params.pop("watermark", False),
            **api_params,
        )

        payload = request.to_dict()
        return self._submit_task(payload)

    def r2v(
        self, prompt: str, reference_path: str, params: dict[str, Any] | None = None
    ) -> tuple[str, dict[str, Any]]:
        api_params = params.copy() if params else {}
        reference_media_dicts = api_params.pop("reference_media", [])
        first_frame_path = api_params.pop("first_frame_path", None)
        main_reference_voice = api_params.pop("reference_voice", None)

        reference_path = self._upload_file_if_needed(reference_path)

        if first_frame_path:
            first_frame_path = self._upload_file_if_needed(first_frame_path)

        if main_reference_voice:
            main_reference_voice = self._upload_file_if_needed(main_reference_voice)

        media: list[MediaItem] = []

        if first_frame_path:
            media.append(MediaItem(type="first_frame", url=first_frame_path))

        main_type = self._detect_media_type(reference_path)
        media.append(MediaItem(
            type=main_type,
            url=reference_path,
            reference_voice=main_reference_voice,
        ))

        for ref in reference_media_dicts:
            ref_path = ref.get("path")
            if not ref_path:
                continue

            ref_path = self._upload_file_if_needed(ref_path)
            ref_type = ref.get("type") or self._detect_media_type(ref_path)

            ref_voice = ref.get("reference_voice")
            if ref_voice:
                ref_voice = self._upload_file_if_needed(ref_voice)

            media.append(MediaItem(
                type=ref_type,
                url=ref_path,
                reference_voice=ref_voice,
            ))

        model = self._model_mappings.get("r2v") or self._model_mappings.get("default") or "wan2.7-r2v-2026-06-12"
        request = DashScopeVideoRequest.for_r2v(
            model=model,
            prompt=prompt,
            media=media,
            negative_prompt=api_params.pop("negative_prompt", None),
            resolution=api_params.pop("resolution", None),
            ratio=api_params.pop("ratio", None),
            duration=api_params.pop("duration", None),
            prompt_extend=api_params.pop("prompt_extend", True),
            watermark=api_params.pop("watermark", False),
            **api_params,
        )

        payload = request.to_dict()
        return self._submit_task(payload)

    @staticmethod
    def _detect_media_type(path: str) -> str:
        path_lower = path.lower()
        if path_lower.endswith((".mp4", ".mov", ".avi", ".mkv")):
            return "reference_video"
        elif path_lower.endswith((".jpg", ".jpeg", ".png", ".bmp", ".webp")):
            return "reference_image"
        else:
            logger.warning(f"无法识别媒体类型，默认当作图片: {path}")
            return "reference_image"

    def extend(
        self, prompt: str, video_path: str, params: dict[str, Any] | None = None
    ) -> tuple[str, dict[str, Any]]:
        api_params = params.copy() if params else {}
        last_frame_path = api_params.pop("last_frame_path", None)

        video_path = self._upload_file_if_needed(video_path)
        if last_frame_path:
            last_frame_path = self._upload_file_if_needed(last_frame_path)

        media: list[MediaItem] = [MediaItem(type="first_clip", url=video_path)]

        if last_frame_path:
            media.append(MediaItem(type="last_frame", url=last_frame_path))

        model = self._model_mappings.get("extend") or self._model_mappings.get("default") or self._model
        request = DashScopeVideoRequest.for_r2v(
            model=model,
            prompt=prompt,
            media=media,
            negative_prompt=api_params.pop("negative_prompt", None),
            resolution=api_params.pop("resolution", None),
            ratio=api_params.pop("ratio", None),
            duration=api_params.pop("duration", None),
            prompt_extend=api_params.pop("prompt_extend", True),
            watermark=api_params.pop("watermark", False),
            **api_params,
        )

        payload = request.to_dict()
        return self._submit_task(payload)

    def check_status(self, task_id: str) -> TaskResult:
        url = f"{self._task_url}/{task_id}"
        resp = requests.get(url, headers=self._headers(), timeout=30)

        if not resp.ok:
            try:
                error_data = resp.json()
                error_detail = error_data.get("message", "") or resp.text
            except Exception:
                error_detail = resp.text
            logger.error(f"DashScope 状态查询失败 ({resp.status_code}): {error_detail}")
            raise RuntimeError(f"DashScope 状态查询错误 ({resp.status_code}): {error_detail}")

        data = resp.json()
        logger.debug(f"状态查询响应：{data}")

        output = data.get("output", {})
        task_status = output.get("task_status", "")

        if task_status == "SUCCEEDED":
            video_url = output.get("video_url", "")
            if not video_url:
                results = output.get("results", [])
                if results and isinstance(results, list):
                    video_url = results[0].get("url", "")
                elif isinstance(results, dict):
                    video_url = results.get("url", "")
            logger.info(f"任务成功，video_url={video_url}")
            return TaskResult(status=TaskStatus.SUCCEEDED, video_url=video_url)

        if task_status == "FAILED":
            code = output.get("code", "")
            message = output.get("message", "未知错误")
            error = f"[{code}] {message}" if code else message
            logger.error(f"任务失败：{error}")
            return TaskResult(status=TaskStatus.FAILED, error_message=error)

        if task_status == "RUNNING":
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
                        progress_callback(downloaded=downloaded, total=total)

        logger.info(f"下载完成：{save_path}")
        return save_path

    def get_model_info(self) -> list[ModelInfo]:
        return [
            ModelInfo(
                name=self._model,
                provider_name=self.provider_name,
                supported_resolutions=["720P", "1080P"],
                supported_ratios=["16:9", "9:16", "1:1", "4:3", "3:4"],
                max_duration=15,
                description="阿里万象 wan2.7 多模态视频生成模型（支持文生视频、图生视频、视频续写）",
            ),
        ]
