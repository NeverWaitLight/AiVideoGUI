from __future__ import annotations

import json
import os
import uuid
from typing import TYPE_CHECKING

from loguru import logger

from config.manager import ConfigManager
from models.enums import GenerateTaskType, GenerateTaskCallerType
from models.generate_task_context import GenerateTaskContext
from models.image_generation_request import ImageGenerationRequest, ImageScene
from prompts.chat_prompt_builder import ChatPromptBuilder
from providers.dashscope_image import DashScopeImageProvider
from providers.image_base import ImageProvider
from service.background.image_generation_worker import (
    BatchImageGenerationWorker,
    ImageGenerationCoordinator,
    _get_image_provider,
    emit_task_failed,
    get_image_signal_emitter,
)
from storage.session_manager import SessionManager
from storage.repositories.generate_task_repository import GenerateTaskRepository
from utils import paths
from utils.path_converter import to_relative_path
from utils.prompt_sanitize import flatten_prompt_text

if TYPE_CHECKING:
    from service.character_service import CharacterService
    from service.chat_service import ChatService
    from service.project_service import ProjectService
    from service.storyboard_service import StoryboardService

_PROVIDER_REGISTRY: dict[str, type[ImageProvider]] = {
    "dashscope": DashScopeImageProvider,
    "dashscope_image": DashScopeImageProvider,
}

# 与项目视频比例对应的 wan 推荐尺寸（width*height）
_ASPECT_RATIO_SIZE_MAP: dict[str, str] = {
    "1:1": "1280*1280",
    "3:4": "1104*1472",
    "4:3": "1472*1104",
    "9:16": "960*1696",
    "16:9": "1696*960",
}

_DEFAULT_IMAGE_SIZE = "1696*960"


def resolve_image_size(aspect_ratio: str) -> str:
    ratio = (aspect_ratio or "").strip()
    return _ASPECT_RATIO_SIZE_MAP.get(ratio, _DEFAULT_IMAGE_SIZE)


class ImageService:

    def __init__(
        self,
        config_manager: ConfigManager,
        session_manager: SessionManager,
        chat_service: "ChatService",
        prompt_builder: ChatPromptBuilder,
        storyboard_service: "StoryboardService",
        character_service: "CharacterService",
        project_service: "ProjectService",
        workspace_root: str,
    ) -> None:
        self._config = config_manager
        self._sm = session_manager
        self._chat_service = chat_service
        self._prompt_builder = prompt_builder
        self._storyboard_service = storyboard_service
        self._character_service = character_service
        self._project_service = project_service
        self._workspace_root = workspace_root
        self._coordinator = ImageGenerationCoordinator()
        self._provider_cache: dict[str, ImageProvider] = {}

    def invalidate_provider_cache(self) -> None:
        if self._provider_cache:
            logger.info("清空 Provider 缓存：image")
        self._provider_cache.clear()

    @property
    def signal_emitter(self):
        return get_image_signal_emitter()

    def _caller_key(self, caller_type: GenerateTaskCallerType, caller_id: str) -> str:
        return f"{caller_type.value}:{caller_id}"

    def _resolve_provider_name(self) -> str:
        provider_name = self._config.settings.default_image_provider or "dashscope"
        if provider_name not in _PROVIDER_REGISTRY:
            logger.warning(f"未知的图片供应商 {provider_name}，回退到 dashscope")
            provider_name = "dashscope"
        return provider_name

    def _create_pending_task(self, request: ImageGenerationRequest) -> tuple[str, int]:
        provider_name = self._resolve_provider_name()
        provider_cfg = self._config.resolve_config_for_type(name=provider_name, provider_type="image")
        if not provider_cfg or not provider_cfg.api_key:
            raise RuntimeError(f"未配置图片生成供应商 {provider_name} 的 API Key，请在设置中配置")

        provider_task_id = str(uuid.uuid4())
        params = request.to_request_params()
        params["config_name"] = provider_name
        request_params = json.dumps(params, ensure_ascii=False)

        task_repo = self._sm.get_repo(repo_class=GenerateTaskRepository)
        self._sm.begin_write()
        try:
            task_id = task_repo.add(
                provider_task_id=provider_task_id,
                provider_name="",
                model_name="",
                local_path="",
                request_params=request_params,
                type=GenerateTaskType.IMAGE,
                caller_type=request.caller_type,
                caller_id=request.caller_id,
                project_id=request.project_id,
            )
            self._sm.commit_write()
        except Exception:
            self._sm.rollback_write()
            raise

        logger.info(
            f"图片生成任务已提交：task_id={provider_task_id}, scene={request.scene.value}, "
            f"caller_type={request.caller_type}, caller_id={request.caller_id}"
        )
        return provider_task_id, task_id

    def _start_worker(self, provider_task_id: str, caller_key: str, wait: bool = False) -> None:
        if wait:
            self.execute_pipeline(provider_task_id)
            return
        self._coordinator.start(self, provider_task_id, caller_key)

    def start_storyboard_design_image(
        self,
        *,
        content: str,
        storyboard_id: int,
        project_id: int,
        scene_number: int,
        shot_number: int,
        shot_size: str = "",
        camera_movement: str = "",
        notes: str = "",
        character_info: str = "",
        visual_style: str = "",
        project_name: str | None = None,
        aspect_ratio: str = "",
        size: str = "",
        wait: bool = False,
    ) -> str:
        caller_type = GenerateTaskCallerType.STORYBOARD
        caller_id = str(storyboard_id)
        caller_key = self._caller_key(caller_type, caller_id)
        if self._coordinator.is_caller_active(caller_key):
            raise RuntimeError("该分镜已有图片生成任务进行中")

        if not size:
            if not aspect_ratio:
                project = self._project_service.get_project(project_id=project_id)
                raw_ratio = getattr(project, "aspect_ratio", "") if project is not None else ""
                aspect_ratio = raw_ratio if isinstance(raw_ratio, str) else ""
            size = resolve_image_size(aspect_ratio)

        local_path = to_relative_path(
            os.path.join(
                paths.projects_dir(self._workspace_root),
                str(project_id),
                f"design-{scene_number}-{shot_number}.png",
            ),
            self._workspace_root,
        )
        request = ImageGenerationRequest(
            scene=ImageScene.STORYBOARD_DESIGN,
            local_path=local_path,
            caller_type=caller_type,
            caller_id=caller_id,
            project_id=project_id,
            project_name=project_name,
            size=size,
            aspect_ratio=aspect_ratio,
            module="storyboard",
            context="分镜设计图生成",
            content=content,
            shot_size=shot_size,
            camera_movement=camera_movement,
            notes=notes,
            character_info=character_info,
            visual_style=visual_style,
        )
        provider_task_id, _task_id = self._create_pending_task(request)
        self._start_worker(provider_task_id, caller_key, wait=wait)
        return provider_task_id

    def start_character_design_image(
        self,
        *,
        character_uuid: str,
        character_name: str,
        description: str,
        project_id: int,
        user_requirement: str = "",
        visual_style: str = "",
        project_name: str | None = None,
        aspect_ratio: str = "",
        size: str = "",
        wait: bool = False,
    ) -> str:
        caller_type = GenerateTaskCallerType.CHARACTER
        caller_id = character_uuid
        caller_key = self._caller_key(caller_type, caller_id)
        if self._coordinator.is_caller_active(caller_key):
            raise RuntimeError("该角色已有图片生成任务进行中")

        if not size:
            if not aspect_ratio:
                project = self._project_service.get_project(project_id=project_id)
                raw_ratio = getattr(project, "aspect_ratio", "") if project is not None else ""
                aspect_ratio = raw_ratio if isinstance(raw_ratio, str) else ""
            size = resolve_image_size(aspect_ratio)

        local_path = to_relative_path(
            os.path.join(
                paths.projects_dir(self._workspace_root),
                str(project_id),
                f"char-{character_uuid}.png",
            ),
            self._workspace_root,
        )
        request = ImageGenerationRequest(
            scene=ImageScene.CHARACTER_DESIGN,
            local_path=local_path,
            caller_type=caller_type,
            caller_id=caller_id,
            project_id=project_id,
            project_name=project_name,
            size=size,
            aspect_ratio=aspect_ratio,
            module="character",
            context=f"角色设计图生成 - {character_name}",
            character_name=character_name,
            description=description,
            user_requirement=user_requirement,
            visual_style=visual_style,
        )
        provider_task_id, _task_id = self._create_pending_task(request)
        self._start_worker(provider_task_id, caller_key, wait=wait)
        return provider_task_id

    def start_cover_image(
        self,
        *,
        project_id: int,
        project_name: str,
        aspect_ratio: str,
        outline_content: str,
        character_info: str,
        visual_style: str = "",
        wait: bool = False,
    ) -> str:
        caller_type = GenerateTaskCallerType.COVER
        caller_id = str(project_id)
        caller_key = self._caller_key(caller_type, caller_id)
        if self._coordinator.is_caller_active(caller_key):
            raise RuntimeError("该项目已有封面生成任务进行中")

        size = resolve_image_size(aspect_ratio)
        local_path = to_relative_path(
            os.path.join(
                paths.projects_dir(self._workspace_root),
                str(project_id),
                f"cover-{project_id}.png",
            ),
            self._workspace_root,
        )
        request = ImageGenerationRequest(
            scene=ImageScene.PROJECT_COVER,
            local_path=local_path,
            caller_type=caller_type,
            caller_id=caller_id,
            project_id=project_id,
            project_name=project_name,
            size=size,
            module="cover",
            context="项目封面图生成",
            aspect_ratio=aspect_ratio,
            outline_content=outline_content,
            cover_character_info=character_info,
            visual_style=visual_style,
        )
        provider_task_id, _task_id = self._create_pending_task(request)
        self._start_worker(provider_task_id, caller_key, wait=wait)
        return provider_task_id

    def start_batch_storyboard_design_images(
        self,
        shot_list: list[dict],
        parent=None,
    ) -> BatchImageGenerationWorker:
        worker = BatchImageGenerationWorker(self, shot_list, parent=parent)
        worker.start()
        return worker

    def execute_pipeline(self, provider_task_id: str) -> str:
        emitter = get_image_signal_emitter()
        caller_type_str = ""
        caller_id = ""

        try:
            task_repo = self._sm.get_repo(repo_class=GenerateTaskRepository)
            task_info = task_repo.get_by_provider_task_id(provider_task_id)
            if not task_info:
                raise RuntimeError(f"任务不存在：{provider_task_id}")

            task_id = task_info["id"]
            request = ImageGenerationRequest.from_request_params(
                json.loads(task_info["request_params"])
            )
            caller_type_str = request.caller_type.value if request.caller_type else ""
            caller_id = request.caller_id

            self._sm.begin_write()
            try:
                task_repo.update_status(task_id, "running")
                self._sm.commit_write()
            except Exception:
                self._sm.rollback_write()
                raise

            emitter.task_started.emit(provider_task_id, caller_type_str, caller_id)
            emitter.task_progress.emit(provider_task_id, "正在生成设计图提示词...")

            messages = self._build_prompt_messages(request)
            prompt, _chat_task_id = self._chat_service.chat(
                messages=messages,
                project_id=request.project_id,
                project_name=request.project_name,
                module=request.module,
                context=f"{request.context} - 提示词生成",
                caller_type=request.caller_type,
                caller_id=request.caller_id,
                parent_ids=str(task_id),
            )
            prompt = flatten_prompt_text(prompt)
            negative_prompt = flatten_prompt_text(request.negative_prompt)

            emitter.task_progress.emit(provider_task_id, "图片生成中，请稍候...")

            provider_name = task_info["provider_name"]
            config_name = json.loads(task_info["request_params"]).get("config_name", provider_name)
            provider = _get_image_provider(self._config, config_name or provider_name, self._provider_cache)

            image_url, _payload, _image_task_id = provider.generate(
                prompt=prompt,
                size=request.size,
                negative_prompt=negative_prompt,
                n=request.n,
                prompt_extend=True,
                watermark=False,
                task_context=GenerateTaskContext(
                    session_manager=self._sm,
                    parent_ids=str(task_id),
                    caller_type=request.caller_type,
                    caller_id=request.caller_id,
                    project_id=request.project_id,
                    project_name=request.project_name,
                    module=request.module,
                    context=request.context,
                    local_path=request.local_path,
                ),
            )

            absolute_path = os.path.join(self._workspace_root, request.local_path)
            os.makedirs(os.path.dirname(absolute_path), exist_ok=True)
            result_path = provider.download(image_url=image_url, save_path=absolute_path)
            relative_path = to_relative_path(result_path, self._workspace_root)

            self._apply_business_update(request, result_path, relative_path)

            self._sm.begin_write()
            try:
                task_repo.update_status(task_id, "succeeded")
                task_repo.mark_completed(task_id)
                self._sm.commit_write()
            except Exception:
                self._sm.rollback_write()
                raise

            logger.info(f"图片生成完成：{relative_path}")
            emitter.task_finished.emit(
                provider_task_id, caller_type_str, caller_id, relative_path
            )
            return relative_path

        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            logger.error(f"图片生成失败：{error_msg}")
            emit_task_failed(
                self._sm, provider_task_id, caller_type_str, caller_id, error_msg
            )
            raise

    def _build_prompt_messages(self, request: ImageGenerationRequest) -> list[dict]:
        if request.scene == ImageScene.STORYBOARD_DESIGN:
            return self._prompt_builder.build_design_image_prompt_messages(
                content=request.content,
                shot_size=request.shot_size,
                camera_movement=request.camera_movement,
                notes=request.notes,
                character_info=request.character_info,
                visual_style=request.visual_style,
                aspect_ratio=request.aspect_ratio,
            )
        if request.scene == ImageScene.CHARACTER_DESIGN:
            return self._prompt_builder.build_character_design_image_prompt_messages(
                character_name=request.character_name,
                description=request.description,
                user_requirement=request.user_requirement,
                visual_style=request.visual_style,
            )
        if request.scene == ImageScene.PROJECT_COVER:
            return self._prompt_builder.build_cover_image_prompt_messages(
                project_name=request.project_name or "",
                aspect_ratio=request.aspect_ratio,
                outline_content=request.outline_content,
                character_info=request.cover_character_info,
                visual_style=request.visual_style,
            )
        raise RuntimeError(f"未知的图片生成场景：{request.scene}")

    def _apply_business_update(
        self,
        request: ImageGenerationRequest,
        absolute_path: str,
        relative_path: str,
    ) -> None:
        if request.caller_type == GenerateTaskCallerType.STORYBOARD:
            self._storyboard_service.update_storyboard(
                storyboard_id=int(request.caller_id),
                design_image=absolute_path,
            )
        elif request.caller_type == GenerateTaskCallerType.CHARACTER:
            self._character_service.update_character(
                character_uuid=request.caller_id,
                design_image=absolute_path,
            )
        elif request.caller_type == GenerateTaskCallerType.COVER:
            project = self._project_service.get_project(project_id=int(request.caller_id))
            if project:
                self._project_service.update_project(
                    project_id=project.id,
                    name=project.name,
                    resolution=project.resolution,
                    aspect_ratio=project.aspect_ratio,
                    cover_image=relative_path,
                    visual_style_id=project.visual_style_id,
                )

    def generate(
        self,
        prompt: str,
        local_path: str,
        size: str = "",
        negative_prompt: str = "",
        n: int = 1,
        project_id: int | None = None,
        project_name: str | None = None,
        module: str = "storyboard",
        context: str | None = None,
        caller_type: GenerateTaskCallerType | None = None,
        caller_id: str = "",
        parent_ids: str = "",
        aspect_ratio: str = "",
    ) -> str:
        """兼容旧测试：直接落库带 prompt 的 IMAGE 任务"""
        if not size:
            size = resolve_image_size(aspect_ratio)
        provider_name = self._resolve_provider_name()
        provider_cfg = self._config.resolve_config_for_type(name=provider_name, provider_type="image")
        if not provider_cfg or not provider_cfg.api_key:
            raise RuntimeError(f"未配置图片生成供应商 {provider_name} 的 API Key，请在设置中配置")

        prompt = flatten_prompt_text(prompt)
        negative_prompt = flatten_prompt_text(negative_prompt)
        provider_task_id = str(uuid.uuid4())

        request_params = json.dumps({
            "scene": ImageScene.STORYBOARD_DESIGN.value,
            "local_path": local_path,
            "caller_type": (caller_type or GenerateTaskCallerType.STORYBOARD).value,
            "caller_id": caller_id,
            "project_id": project_id,
            "project_name": project_name,
            "size": size,
            "negative_prompt": negative_prompt,
            "n": n,
            "module": module,
            "context": context,
            "config_name": provider_name,
            "prompt": prompt,
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
        return provider_task_id
