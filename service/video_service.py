from __future__ import annotations

import json
from loguru import logger
import uuid
from datetime import datetime
from typing import Any

from PySide6.QtCore import QObject

from config.manager import ConfigManager
from models.enums import MessageStatus
from providers.video_base import VideoProvider
from providers.dashscope_video import DashScopeVideoProvider
from providers.seedance_video import SeedanceVideoProvider
from storage.session_manager import SessionManager
from storage.repositories.generate_task_repository import GenerateTaskRepository
from utils.ai_request_logger import AIRequestLogger

_PROVIDER_REGISTRY: dict[str, type[VideoProvider]] = {
    "dashscope": DashScopeVideoProvider,
    "seedance": SeedanceVideoProvider,
}

class VideoService(QObject):

    def __init__(
        self,
        session_manager: SessionManager,
        config: ConfigManager,
        parent: QObject | None = None,
        ai_request_logger: AIRequestLogger | None = None,
    ) -> None:
        super().__init__(parent)
        self._sm = session_manager
        self._config = config
        self._providers: dict[str, VideoProvider] = {}
        self._ai_logger = ai_request_logger

    def get_provider(self, name: str) -> VideoProvider:
        if name in self._providers:
            return self._providers[name]
        cfg = self._config.get_provider_config(name=name, provider_type="video")
        if cfg is None:
            raise KeyError(f"未配置的 Provider：{name}")
        cls = _PROVIDER_REGISTRY.get(name)
        if cls is None:
            raise KeyError(f"未注册的 Provider：{name}")
        provider = cls(cfg)

        if hasattr(provider, "set_session_manager"):
            provider.set_session_manager(self._sm)

        self._providers[name] = provider
        return provider

    def submit_task(
        self,
        prompt: str,
        provider_name: str,
        params: dict[str, Any] | None = None,
        save_path: str = "",
        storyboard_id: int = 0,
        reference_image: str = "",
        reference_images: list[str] | None = None,
        project_id: int | None = None,
        project_name: str | None = None,
    ) -> str:
        provider = self.get_provider(provider_name)

        if reference_images:
            main_ref = reference_images[0]
            if len(reference_images) > 1:
                params = (params or {}).copy()
                params["reference_media"] = [
                    {"path": p, "type": "reference_image"}
                    for p in reference_images[1:]
                ]
            provider_task_id, request_details = provider.r2v(prompt=prompt, reference_path=main_ref, params=params)
            logger.info(f"使用参考生视频 (r2v)：{len(reference_images)} 张参考图")
            request_type = "video_generation_r2v"
            context = f"参考图生成视频 (r2v, {len(reference_images)}张)"
        elif reference_image:
            provider_task_id, request_details = provider.r2v(prompt=prompt, reference_path=reference_image, params=params)
            logger.info(f"使用参考生视频 (r2v)：reference_image={reference_image}")
            request_type = "video_generation_r2v"
            context = "参考图生成视频 (r2v)"
        else:
            provider_task_id, request_details = provider.t2v(prompt=prompt, params=params)
            logger.info(f"使用文生视频 (t2v)")
            request_type = "video_generation_t2v"
            context = "文生视频 (t2v)"

        # 记录 AI 请求（与文本/图片模型日志格式一致，包含完整 HTTP 请求信息）
        if self._ai_logger:
            self._ai_logger.log_request(
                request_type=request_type,
                module="storyboard",
                payload=request_details,
                response={"provider_task_id": provider_task_id},
                project_id=project_id,
                project_name=project_name,
                context=context,
            )

        task_repo = self._sm.get_repo(GenerateTaskRepository)

        self._sm.begin_write()
        try:
            generate_task_id = task_repo.add(
                provider_task_id=provider_task_id,
                provider_name=provider_name,
                model_name=provider._config.default_model,
                save_path=save_path,
                request_params=json.dumps(request_details["json"], ensure_ascii=False),
                storyboard_id=storyboard_id,
            )

            self._sm.commit_write()

            logger.info(
                "任务已提交 provider_task=%s generate_task=%s provider=%s save_path=%s storyboard_id=%s",
                provider_task_id,
                generate_task_id,
                provider_name,
                save_path,
                storyboard_id,
            )
            return provider_task_id
        except Exception as e:
            self._sm.rollback_write()
            logger.error(f"提交任务失败: {e}")
            raise
