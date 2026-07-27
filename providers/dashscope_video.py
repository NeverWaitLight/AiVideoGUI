"""阿里万象 DashScope 视频生成 Provider。"""

import logging
import os
import re
from pathlib import Path
from typing import Any, Callable

import requests

from models.data_models import ModelInfo, ProviderConfig, TaskResult, TaskStatus
from providers.dashscope_oss_uploader import DashScopeOSSUploader
from providers.video_base import VideoProvider

logger = logging.getLogger(__name__)


class DashScopeVideoProvider(VideoProvider):
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
        self._oss_uploader = DashScopeOSSUploader(self._api_key)
        self._db_manager = None  # 延迟注入，由外部设置

    def set_database_manager(self, db_manager) -> None:
        """注入 DatabaseManager 实例（用于 OSS 缓存）"""
        self._db_manager = db_manager

    @staticmethod
    def _is_local_file(path: str) -> bool:
        """判断是否为本地文件路径（而非 URL 或 oss:// 前缀）"""
        if not path:
            return False
        # 排除已经是 URL 或 oss:// 的情况
        if path.startswith(("http://", "https://", "oss://")):
            return False
        # 检查是否为本地文件路径
        return Path(path).exists()

    def _upload_file_if_needed(self, file_path: str) -> str:
        """
        如果是本地文件，上传到 OSS 并返回 oss:// URL；否则直接返回原路径。

        优先使用数据库缓存，缓存命中时复用 URL，缓存未命中时上传并保存缓存。

        Args:
            file_path: 文件路径（本地路径、URL 或 oss://）

        Returns:
            oss:// URL 或原路径
        """
        if not self._is_local_file(file_path):
            return file_path

        logger.debug(f"检测到本地文件: {file_path}")

        # 1. 尝试从数据库缓存获取
        if self._db_manager:
            cache = self._db_manager.get_oss_cache(file_path, self._model)
            if cache:
                logger.info(f"命中 OSS 缓存: {file_path} -> {cache['oss_url']}")
                return cache["oss_url"]

        # 2. 缓存未命中，上传文件
        logger.info(f"上传文件到 OSS: {file_path}")
        oss_url, expire_time = self._oss_uploader.upload(file_path, self._model)

        # 3. 保存到数据库缓存
        if self._db_manager:
            try:
                self._db_manager.save_oss_cache(file_path, self._model, oss_url)
            except Exception as e:
                logger.warning(f"保存 OSS 缓存失败（不影响任务提交）: {e}")

        return oss_url

    def _headers(self, *, async_mode: bool = False) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        if async_mode:
            headers["X-DashScope-Async"] = "enable"
        # 添加 OSS 资源解析头（用于 oss:// URL）
        headers["X-DashScope-OssResourceResolve"] = "enable"
        return headers

    def build_payload(self, prompt: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """构建提交给 DashScope API 的完整请求体（不发起网络请求）。

        新版 wan2.7 API 协议直接使用分辨率档位标签（如 "720P"）和宽高比（如 "16:9"），
        无需转换为具体像素值。

        支持的参数：
        - resolution: 分辨率档位 ("720P" | "1080P")
        - ratio: 宽高比 ("16:9" | "9:16" | "1:1" | "4:3" | "3:4")
        - duration: 视频时长 (2-15秒)
        - prompt_extend: 智能改写提示词 (bool)
        - watermark: 添加水印 (bool)
        - negative_prompt: 反向提示词 (str, 添加到 input 中)
        - audio_url: 自定义音频 URL (str, 添加到 input 中)
        - seed: 随机数种子 (int)
        """
        api_params = params.copy() if params else {}

        # 构建 input 对象
        input_obj = {"prompt": prompt}

        # negative_prompt 和 audio_url 属于 input 字段，需要从 parameters 中提取
        if "negative_prompt" in api_params:
            input_obj["negative_prompt"] = api_params.pop("negative_prompt")

        if "audio_url" in api_params:
            input_obj["audio_url"] = api_params.pop("audio_url")

        # 其余参数（resolution, ratio, duration, prompt_extend, watermark, seed）直接传递到 parameters
        return {
            "model": self._model,
            "input": input_obj,
            "parameters": api_params,
        }

    def _submit_task(self, payload: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        """提交任务到 DashScope API，返回 (task_id, payload)。"""
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
        return task_id, payload

    def t2v(self, prompt: str, params: dict[str, Any] | None = None) -> tuple[str, dict[str, Any]]:
        """文生视频：提交文本生成视频任务，返回 (task_id, 完整请求参数)。"""
        payload = self.build_payload(prompt, params)
        return self._submit_task(payload)

    def p2v(
        self, prompt: str, image_path: str, params: dict[str, Any] | None = None
    ) -> tuple[str, dict[str, Any]]:
        """图生视频：提交图片+文本生成视频任务，返回 (task_id, 完整请求参数)。

        支持两种模式：
        1. 首帧生视频 - 仅传入 image_path
        2. 首尾帧生视频 - 传入 image_path + params["last_frame_path"]

        参数：
        - image_path: 首帧图片路径（URL、本地路径或 oss://，本地路径会自动上传）
        - params["last_frame_path"]: 尾帧图片路径（可选，URL、本地路径或 oss://）
        - params["driving_audio_path"]: 驱动音频路径（可选，URL、本地路径或 oss://）
        """
        # 复制 params 并提取 media 相关参数
        api_params = params.copy() if params else {}
        last_frame_path = api_params.pop("last_frame_path", None)
        driving_audio_path = api_params.pop("driving_audio_path", None)

        # 上传本地文件（如果需要）
        image_path = self._upload_file_if_needed(image_path)
        if last_frame_path:
            last_frame_path = self._upload_file_if_needed(last_frame_path)
        if driving_audio_path:
            driving_audio_path = self._upload_file_if_needed(driving_audio_path)

        # 构建基础 payload（此时 api_params 已移除 media 相关参数）
        payload = self.build_payload(prompt, api_params)

        # 构建 media 数组
        media = [{"type": "first_frame", "url": image_path}]

        # 添加尾帧（如果提供）
        if last_frame_path:
            media.append({"type": "last_frame", "url": last_frame_path})

        # 添加驱动音频（如果提供）
        if driving_audio_path:
            media.append({"type": "driving_audio", "url": driving_audio_path})

        # 注入 media 到 payload
        payload["input"]["media"] = media

        # 提交任务
        return self._submit_task(payload)

    def r2v(
        self, prompt: str, reference_path: str, params: dict[str, Any] | None = None
    ) -> tuple[str, dict[str, Any]]:
        """参考生视频：提交参考素材+文本生成视频任务，返回 (task_id, 完整请求参数)。"""
        raise NotImplementedError("DashScope r2v 尚未实现")

    def extend(
        self, prompt: str, video_path: str, params: dict[str, Any] | None = None
    ) -> tuple[str, dict[str, Any]]:
        """视频续写：基于已有视频继续生成后续内容，返回 (task_id, 完整请求参数)。

        支持两种模式：
        1. 视频续写 - 仅传入 video_path
        2. 视频+尾帧续写 - 传入 video_path + params["last_frame_path"]

        参数：
        - video_path: 首段视频路径（URL、本地路径或 oss://，本地路径会自动上传）
        - params["last_frame_path"]: 尾帧图片路径（可选，URL、本地路径或 oss://）

        注意：duration 参数表示最终输出视频的总时长（包含输入视频时长）
        """
        # 复制 params 并提取 media 相关参数
        api_params = params.copy() if params else {}
        last_frame_path = api_params.pop("last_frame_path", None)

        # 上传本地文件（如果需要）
        video_path = self._upload_file_if_needed(video_path)
        if last_frame_path:
            last_frame_path = self._upload_file_if_needed(last_frame_path)

        # 构建基础 payload（此时 api_params 已移除 media 相关参数）
        payload = self.build_payload(prompt, api_params)

        # 构建 media 数组
        media = [{"type": "first_clip", "url": video_path}]

        # 添加尾帧（如果提供）
        if last_frame_path:
            media.append({"type": "last_frame", "url": last_frame_path})

        # 注入 media 到 payload
        payload["input"]["media"] = media

        # 提交任务
        return self._submit_task(payload)

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
            video_url = output.get("video_url", "")
            if not video_url:
                results = output.get("results", [])
                if results and isinstance(results, list):
                    video_url = results[0].get("url", "")
                elif isinstance(results, dict):
                    video_url = results.get("url", "")
            logger.info("任务成功，video_url=%s", video_url)
            return TaskResult(status=TaskStatus.SUCCEEDED, video_url=video_url)

        if task_status == "FAILED":
            code = output.get("code", "")
            message = output.get("message", "未知错误")
            error = f"[{code}] {message}" if code else message
            logger.error("任务失败：%s", error)
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
                supported_resolutions=["720P", "1080P"],  # wan2.7 仅支持 720P 和 1080P
                supported_ratios=["16:9", "9:16", "1:1", "4:3", "3:4"],  # 支持5种宽高比
                max_duration=15,
                description="阿里万象 wan2.7 多模态视频生成模型（支持文生视频、图生视频、视频续写）",
            ),
        ]
