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
from storage.repositories.active_task_repository import ActiveTaskRepository

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
    ) -> None:
        super().__init__(parent)
        self._sm = session_manager
        self._config = config
        self._providers: dict[str, VideoProvider] = {}

    def get_provider(self, name: str) -> VideoProvider:
        if name in self._providers:
            return self._providers[name]
        cfg = self._config.get_provider(name)
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
    ) -> str:
        provider = self.get_provider(provider_name)

        if reference_image:
            provider_task_id, request_params = provider.r2v(prompt, reference_image, params)
            logger.info(f"使用参考生视频 (r2v)：reference_image={reference_image}")
        else:
            provider_task_id, request_params = provider.t2v(prompt, params)
            logger.info(f"使用文生视频 (t2v)")

        task_repo = self._sm.get_repo(ActiveTaskRepository)

        self._sm.begin_write()
        try:
            active_task_id = task_repo.add(
                provider_task_id=provider_task_id,
                provider_name=provider_name,
                model_name=provider._config.default_model,
                save_path=save_path,
                request_params=json.dumps(request_params, ensure_ascii=False),
                storyboard_id=storyboard_id,
            )

            self._sm.commit_write()

            logger.info(
                "任务已提交 provider_task=%s active_task=%s provider=%s save_path=%s storyboard_id=%s",
                provider_task_id,
                active_task_id,
                provider_name,
                save_path,
                storyboard_id,
            )
            return provider_task_id
        except Exception as e:
            self._sm.rollback_write()
            logger.error(f"提交任务失败: {e}")
            raise
