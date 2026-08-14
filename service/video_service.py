from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QObject
from loguru import logger

from config.manager import ConfigManager
from models.enums import GenerateTaskType, GenerateTaskCallerType
from models.exceptions import MissingConfigError
from providers.dashscope_video import DashScopeVideoProvider
from providers.seedance_video import SeedanceVideoProvider
from providers.video_base import VideoProvider
from storage.repositories.generate_task_repository import GenerateTaskRepository
from storage.session_manager import SessionManager

if TYPE_CHECKING:
    from models.scene import Scene
    from models.storyboard import Storyboard
    from service.chat_service import ChatService

_PROVIDER_REGISTRY: dict[str, type[VideoProvider]] = {
    "dashscope": DashScopeVideoProvider,
    "seedance": SeedanceVideoProvider,
}


class VideoService(QObject):

    def __init__(
        self,
        session_manager: SessionManager,
        config: ConfigManager,
        chat_service: "ChatService",
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._sm = session_manager
        self._config = config
        self._chat_service = chat_service
        self._providers: dict[str, VideoProvider] = {}

    def get_provider(self, name: str) -> VideoProvider:
        if name in self._providers:
            return self._providers[name]
        cfg = self._config.get_provider_config(name=name, provider_type="video")
        if cfg is None:
            raise KeyError(f"未配置的 Provider：{name}")
        cls = _PROVIDER_REGISTRY.get(name)
        if cls is None:
            raise KeyError(f"未注册的 Provider：{name}")

        try:
            provider = cls(cfg)
        except MissingConfigError as e:
            logger.error(f"Provider 配置不完整：{e}")
            raise KeyError(f"Provider '{name}' 配置不完整，请在设置中补全必需字段") from e

        if hasattr(provider, "set_session_manager"):
            provider.set_session_manager(self._sm)

        self._providers[name] = provider
        return provider

    def submit_shot_video(
        self,
        storyboard: "Storyboard",
        provider_name: str,
        local_path: str = "",
        scene: "Scene | None" = None,
        prev_shot: "Storyboard | None" = None,
        next_shot: "Storyboard | None" = None,
        reference_images: list[str] | None = None,
        reference_images_info: list[dict[str, str]] | None = None,
        visual_style: str | None = None,
        params: dict[str, Any] | None = None,
        project_id: int | None = None,
        project_name: str | None = None,
        clean_prompt: bool = True,
    ) -> str:
        from prompts.video_prompt_builder import VideoPromptBuilder

        raw_prompt = VideoPromptBuilder.build_shot_prompt(
            storyboard,
            scene,
            prev_shot,
            next_shot,
            reference_images=reference_images_info,
            visual_style=visual_style,
        )

        prompt = raw_prompt
        if clean_prompt:
            try:
                prompt, _ = self._chat_service.clean_video_prompt(
                    raw_prompt,
                    project_id=project_id,
                    project_name=project_name,
                )
                prompt = prompt.strip()
            except Exception:
                logger.error("视频提示词清理失败，使用原始提示词")
                prompt = raw_prompt

        return self.submit_task(
            prompt=prompt,
            provider_name=provider_name,
            params=params,
            local_path=local_path,
            storyboard_id=storyboard.id,
            reference_images=reference_images,
            project_id=project_id,
            project_name=project_name,
        )

    def submit_task(
        self,
        prompt: str,
        provider_name: str,
        params: dict[str, Any] | None = None,
        local_path: str = "",
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
        elif reference_image:
            provider_task_id, request_details = provider.r2v(prompt=prompt, reference_path=reference_image, params=params)
            logger.info(f"使用参考生视频 (r2v)：reference_image={reference_image}")
        else:
            provider_task_id, request_details = provider.t2v(prompt=prompt, params=params)
            logger.info("使用文生视频 (t2v)")

        task_repo = self._sm.get_repo(GenerateTaskRepository)

        self._sm.begin_write()
        try:
            generate_task_id = task_repo.add(
                provider_task_id=provider_task_id,
                provider_name=provider_name,
                model_name=provider._config.default_model,
                local_path=local_path,
                request_params=json.dumps(request_details["json"], ensure_ascii=False),
                type=GenerateTaskType.VIDEO,
                caller_type=GenerateTaskCallerType.STORYBOARD if storyboard_id else None,
                caller_id=str(storyboard_id) if storyboard_id else "",
                project_id=project_id,
            )

            self._sm.commit_write()

            logger.info(
                "任务已提交 provider_task=%s generate_task=%s provider=%s local_path=%s project_id=%s caller_type=%s caller_id=%s",
                provider_task_id,
                generate_task_id,
                provider_name,
                local_path,
                project_id,
                "storyboard" if storyboard_id else None,
                storyboard_id or "",
            )
            return provider_task_id
        except Exception as e:
            self._sm.rollback_write()
            logger.error(f"提交任务失败: {e}")
            raise
