from __future__ import annotations

import json
import uuid
from typing import TYPE_CHECKING

from loguru import logger

from config.manager import ConfigManager
from models.enums import GenerateTaskType, GenerateTaskCallerType
from providers.dashscope_image import DashScopeImageProvider
from providers.image_base import ImageProvider
from storage.session_manager import SessionManager
from storage.repositories.generate_task_repository import GenerateTaskRepository
from utils.prompt_sanitize import flatten_prompt_text

if TYPE_CHECKING:
    from service.chat_service import ChatService

_PROVIDER_REGISTRY: dict[str, type[ImageProvider]] = {
    "dashscope": DashScopeImageProvider,
    "dashscope_image": DashScopeImageProvider,
}


_ASPECT_RATIO_SIZE_MAP: dict[str, str] = {
    "16:9": "1696*960",
    "9:16": "960*1696",
    "1:1": "1280*1280",
    "4:3": "1472*1104",
    "3:4": "1104*1472",
}


class ImageService:

    def __init__(
        self,
        config_manager: ConfigManager,
        session_manager: SessionManager,
        chat_service: "ChatService",
    ) -> None:
        self._config = config_manager
        self._sm = session_manager
        self._chat_service = chat_service
        self._providers: dict[str, ImageProvider] = {}

    def _get_provider(self) -> ImageProvider:
        provider_name = self._config.settings.default_image_provider or "dashscope"

        if provider_name not in _PROVIDER_REGISTRY:
            logger.warning(f"未知的图片供应商 {provider_name}，回退到 dashscope")
            provider_name = "dashscope"

        if provider_name in self._providers:
            return self._providers[provider_name]

        provider_cfg = self._config.resolve_config_for_type(name=provider_name, provider_type="image")
        if not provider_cfg or not provider_cfg.api_key:
            raise RuntimeError(f"未配置图片生成供应商 {provider_name} 的 API Key，请在设置中配置")

        cls = _PROVIDER_REGISTRY.get(provider_name)

        provider = cls(provider_cfg)
        self._providers[provider_name] = provider
        logger.info(f"初始化图片生成 Provider：{provider_name}")
        return provider

    def generate_design_image(
        self,
        content: str,
        local_path: str,
        shot_size: str = "",
        camera_movement: str = "",
        notes: str = "",
        character_info: str = "",
        visual_style: str = "",
        size: str = "1696*960",
        project_id: int | None = None,
        project_name: str | None = None,
        caller_id: str = "",
    ) -> tuple[str, str]:
        prompt, chat_task_id = self._chat_service.generate_design_image_prompt(
            content=content,
            shot_size=shot_size,
            camera_movement=camera_movement,
            notes=notes,
            character_info=character_info,
            visual_style=visual_style,
            project_id=project_id,
            project_name=project_name,
        )
        provider_task_id = self.generate(
            prompt=prompt,
            local_path=local_path,
            size=size,
            project_id=project_id,
            project_name=project_name,
            module="storyboard",
            context="分镜设计图生成",
            caller_type=GenerateTaskCallerType.STORYBOARD,
            caller_id=caller_id,
            parent_ids=str(chat_task_id),
        )
        return provider_task_id, str(chat_task_id)

    def generate_character_design_image(
        self,
        character_name: str,
        description: str,
        local_path: str,
        user_requirement: str = "",
        visual_style: str = "",
        size: str = "1280*1280",
        project_id: int | None = None,
        project_name: str | None = None,
        caller_id: str = "",
    ) -> tuple[str, str]:
        prompt, chat_task_id = self._chat_service.generate_character_design_image_prompt(
            character_name=character_name,
            description=description,
            user_requirement=user_requirement,
            visual_style=visual_style,
            project_id=project_id,
            project_name=project_name,
        )
        provider_task_id = self.generate(
            prompt=prompt,
            local_path=local_path,
            size=size,
            project_id=project_id,
            project_name=project_name,
            module="character",
            context=f"角色设计图生成 - {character_name}",
            caller_type=GenerateTaskCallerType.CHARACTER,
            caller_id=caller_id,
            parent_ids=str(chat_task_id),
        )
        return provider_task_id, str(chat_task_id)

    def generate_cover_image(
        self,
        project_name: str,
        aspect_ratio: str,
        outline_content: str,
        character_info: str,
        local_path: str,
        visual_style: str = "",
        project_id: int | None = None,
    ) -> tuple[str, str]:
        prompt, chat_task_id = self._chat_service.generate_cover_image_prompt(
            project_name=project_name,
            aspect_ratio=aspect_ratio,
            outline_content=outline_content,
            character_info=character_info,
            visual_style=visual_style,
            project_id=project_id,
        )
        size = _ASPECT_RATIO_SIZE_MAP.get(aspect_ratio, "1696*960")
        provider_task_id = self.generate(
            prompt=prompt,
            local_path=local_path,
            size=size,
            project_id=project_id,
            project_name=project_name,
            module="cover",
            context="项目封面图生成",
            caller_type=GenerateTaskCallerType.COVER,
            caller_id=str(project_id) if project_id else "",
            parent_ids=str(chat_task_id),
        )
        return provider_task_id, str(chat_task_id)

    def generate(
        self,
        prompt: str,
        local_path: str,
        size: str = "1696*960",
        negative_prompt: str = "",
        n: int = 1,
        project_id: int | None = None,
        project_name: str | None = None,
        module: str = "storyboard",
        context: str | None = None,
        caller_type: GenerateTaskCallerType | None = None,
        caller_id: str = "",
        parent_ids: str = "",
    ) -> str:
        """提交图片生成任务到数据库，返回 provider_task_id"""
        provider_name = self._config.settings.default_image_provider or "dashscope"
        prompt = flatten_prompt_text(prompt)
        negative_prompt = flatten_prompt_text(negative_prompt)

        provider_cfg = self._config.resolve_config_for_type(name=provider_name, provider_type="image")
        if not provider_cfg or not provider_cfg.api_key:
            raise RuntimeError(f"未配置图片生成供应商 {provider_name} 的 API Key，请在设置中配置")

        provider_task_id = str(uuid.uuid4())

        request_params = json.dumps({
            "prompt": prompt,
            "size": size,
            "negative_prompt": negative_prompt,
            "n": n,
            "module": module,
            "context": context,
            "config_name": provider_name,
        }, ensure_ascii=False)

        task_repo = self._sm.get_repo(repo_class=GenerateTaskRepository)
        self._sm.begin_write()
        try:
            task_repo.add(
                provider_task_id=provider_task_id,
                provider_name=provider_name,
                model_name=provider_cfg.default_model or "wan2.6-t2i",
                local_path=local_path,
                request_params=request_params,
                type=GenerateTaskType.IMAGE,
                caller_type=caller_type,
                caller_id=caller_id,
                project_id=project_id,
                parent_ids=parent_ids,
            )
            self._sm.commit_write()
        except Exception:
            self._sm.rollback_write()
            raise

        logger.info(
            f"图片生成任务已提交：task_id={provider_task_id}, provider={provider_name}, "
            f"size={size}, caller_type={caller_type}, "
            f"caller_id={caller_id}, parent_ids={parent_ids}"
        )
        return provider_task_id
