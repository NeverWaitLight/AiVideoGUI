from __future__ import annotations

import json
import os
import time
import uuid
from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QObject
from loguru import logger

from config.manager import ConfigManager
from models.enums import GenerateTaskType, GenerateTaskCallerType, TakeStatus
from models.generate_task_context import GenerateTaskContext
from models.storyboard_take import StoryboardTake
from models.video_generation_request import VideoGenerationRequest, VideoScene
from models.exceptions import MissingConfigError
from providers.dashscope_video import DashScopeVideoProvider
from providers.video_base import VideoProvider
from service.background.video_generation_worker import (
    VideoGenerationCoordinator,
    emit_video_task_failed,
    get_video_signal_emitter,
)
from storage.repositories.generate_task_repository import GenerateTaskRepository
from storage.repositories.storyboard_take_repository import StoryboardTakeRepository
from storage.session_manager import SessionManager
from utils import paths
from utils.path_converter import to_relative_path
from utils.prompt_sanitize import flatten_prompt_text

if TYPE_CHECKING:
    from models.scene import Scene
    from models.storyboard import Storyboard
    from prompts.chat_prompt_builder import ChatPromptBuilder
    from service.chat_service import ChatService
    from service.screenplay_service import ScreenplayService
    from service.storyboard_service import StoryboardService

_PROVIDER_REGISTRY: dict[str, type[VideoProvider]] = {
    "dashscope": DashScopeVideoProvider,
}


class VideoService(QObject):

    def __init__(
        self,
        session_manager: SessionManager,
        config: ConfigManager,
        chat_service: "ChatService",
        prompt_builder: "ChatPromptBuilder",
        storyboard_service: "StoryboardService",
        screenplay_service: "ScreenplayService",
        workspace_root: str,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._sm = session_manager
        self._config = config
        self._chat_service = chat_service
        self._prompt_builder = prompt_builder
        self._storyboard_service = storyboard_service
        self._screenplay_service = screenplay_service
        self._workspace_root = workspace_root
        self._providers: dict[str, VideoProvider] = {}
        self._coordinator = VideoGenerationCoordinator()

    def invalidate_provider_cache(self) -> None:
        if self._providers:
            logger.info("清空 Provider 缓存：video")
        self._providers.clear()

    @property
    def signal_emitter(self):
        return get_video_signal_emitter()

    def _caller_key(self, storyboard_id: int) -> str:
        return f"{GenerateTaskCallerType.STORYBOARD.value}:{storyboard_id}"

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

    def start_shot_video(
        self,
        request: VideoGenerationRequest,
        wait_submit: bool = False,
    ) -> str:
        caller_key = self._caller_key(request.storyboard_id)
        if self._coordinator.is_caller_active(caller_key):
            raise RuntimeError("该分镜已有视频生成任务进行中")

        pending_provider_task_id, _task_id = self._create_pending_task(request)
        emitter = get_video_signal_emitter()
        emitter.video_generation_started.emit(str(request.storyboard_id))
        emitter.take_created.emit()

        if wait_submit:
            self.execute_submit_pipeline(pending_provider_task_id)
            # 完成信号使用父任务 pending UUID，批量等待必须与之对齐
            return pending_provider_task_id

        self._coordinator.start(self, pending_provider_task_id, caller_key)
        return pending_provider_task_id

    def _create_pending_task(self, request: VideoGenerationRequest) -> tuple[str, int]:
        _provider = self.get_provider(request.provider_name)
        pending_provider_task_id = str(uuid.uuid4())
        request_params = json.dumps(request.to_request_params(), ensure_ascii=False)

        task_repo = self._sm.get_repo(GenerateTaskRepository)
        self._sm.begin_write()
        try:
            take_number = None
            local_path = request.local_path
            if request.storyboard_id > 0 and request.project_id:
                take_repo = self._sm.get_repo(StoryboardTakeRepository)
                take_number = take_repo.get_next_number(request.storyboard_id)
                if not local_path:
                    local_path = to_relative_path(
                        os.path.join(
                            paths.projects_dir(paths.workspace_root()),
                            str(request.project_id),
                            f"{request.scene_number}-{request.shot_number}-{take_number}.mp4",
                        ),
                        paths.workspace_root(),
                    )
                    request.local_path = local_path

            generate_task_id = task_repo.add(
                provider_task_id=pending_provider_task_id,
                provider_name="",
                model_name="",
                local_path="",
                request_params=request_params,
                type=GenerateTaskType.VIDEO,
                caller_type=GenerateTaskCallerType.STORYBOARD,
                caller_id=str(request.storyboard_id),
                project_id=request.project_id,
            )

            if request.storyboard_id > 0 and take_number is not None:
                take_repo = self._sm.get_repo(StoryboardTakeRepository)
                now_ms = int(time.time() * 1000)
                take_repo.create(
                    dto=StoryboardTake(
                        storyboard_id=request.storyboard_id,
                        number=take_number,
                        media_file_id="",
                        generate_task_id=generate_task_id,
                        status=TakeStatus.CANDIDATE,
                        created_at=now_ms,
                        updated_at=now_ms,
                    )
                )
                logger.info(
                    f"创建 pending 视频任务：storyboard_id={request.storyboard_id}, "
                    f"number={take_number}, generate_task_id={generate_task_id}"
                )

            self._sm.commit_write()
        except Exception:
            self._sm.rollback_write()
            raise

        logger.info(
            "视频任务已创建 pending provider_task=%s generate_task=%s storyboard_id=%s",
            pending_provider_task_id,
            generate_task_id,
            request.storyboard_id,
        )
        return pending_provider_task_id, generate_task_id

    def execute_submit_pipeline(self, pending_provider_task_id: str) -> str:
        emitter = get_video_signal_emitter()
        caller_type_str = GenerateTaskCallerType.STORYBOARD.value
        caller_id = ""

        try:
            task_repo = self._sm.get_repo(GenerateTaskRepository)
            task_info = task_repo.get_by_provider_task_id(pending_provider_task_id)
            if not task_info:
                raise RuntimeError(f"任务不存在：{pending_provider_task_id}")

            task_id = task_info["id"]
            request = VideoGenerationRequest.from_request_params(
                json.loads(task_info["request_params"])
            )
            caller_id = str(request.storyboard_id)

            self._sm.begin_write()
            try:
                task_repo.update_status(task_id, "running")
                self._sm.commit_write()
            except Exception:
                self._sm.rollback_write()
                raise

            emitter.task_started.emit(pending_provider_task_id, caller_type_str, caller_id)
            emitter.task_progress.emit(pending_provider_task_id, "正在组装视频提示词...")

            storyboard = self._storyboard_service.get_storyboard(storyboard_id=request.storyboard_id)
            if not storyboard:
                raise RuntimeError(f"分镜不存在：{request.storyboard_id}")

            scene = None
            if request.scene_id:
                scene = self._screenplay_service.get_scene(request.scene_id)
            elif storyboard.scene_id:
                scene = self._screenplay_service.get_scene(storyboard.scene_id)

            prev_shot = (
                self._storyboard_service.get_storyboard(storyboard_id=request.prev_shot_id)
                if request.prev_shot_id
                else None
            )
            next_shot = (
                self._storyboard_service.get_storyboard(storyboard_id=request.next_shot_id)
                if request.next_shot_id
                else None
            )

            raw_prompt = self._prompt_builder.assemble_video_shot_prompt(
                storyboard,
                scene,
                prev_shot,
                next_shot,
                reference_images=request.reference_images_info or None,
                visual_style=request.visual_style,
            )

            prompt = raw_prompt
            if request.clean_prompt:
                emitter.task_progress.emit(pending_provider_task_id, "正在优化视频提示词...")
                try:
                    messages = self._prompt_builder.build_video_prompt_clean_messages(raw_prompt)
                    prompt, _chat_task_id = self._chat_service.chat(
                        messages=messages,
                        project_id=request.project_id,
                        project_name=request.project_name,
                        module="storyboard",
                        context="视频提示词清理",
                        caller_type=GenerateTaskCallerType.STORYBOARD,
                        caller_id=caller_id,
                        parent_ids=str(task_id),
                    )
                    prompt = prompt.strip()
                except Exception:
                    logger.error("视频提示词清理失败，使用原始提示词")
                    prompt = raw_prompt

            prompt = flatten_prompt_text(prompt)
            emitter.task_progress.emit(pending_provider_task_id, "正在提交视频生成任务...")

            task_context = GenerateTaskContext(
                session_manager=self._sm,
                parent_ids=str(task_id),
                caller_type=GenerateTaskCallerType.STORYBOARD,
                caller_id=caller_id,
                project_id=request.project_id,
                project_name=request.project_name,
                module="storyboard",
                context="视频生成提交",
                local_path=request.local_path,
            )
            provider_task_id, _request_details, _child_task_id = self._call_provider(
                prompt=prompt,
                provider_name=request.provider_name,
                params=request.params,
                reference_images=request.reference_images,
                reference_image=request.reference_image,
                prev_shot_last_frame=request.prev_shot_last_frame,
                task_context=task_context,
            )

            self._sm.begin_write()
            try:
                task_repo.update_status(task_id, "pending")
                self._sm.commit_write()
            except Exception:
                self._sm.rollback_write()
                raise

            logger.info(
                "视频任务已提交 provider_task=%s generate_task=%s storyboard_id=%s",
                provider_task_id,
                task_id,
                request.storyboard_id,
            )
            emitter.submit_finished.emit(pending_provider_task_id, provider_task_id)
            return provider_task_id

        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            logger.error(f"视频提交阶段失败：{error_msg}")
            emit_video_task_failed(
                self._sm, pending_provider_task_id, caller_type_str, caller_id, error_msg
            )
            if caller_id:
                emitter.video_generation_failed.emit(caller_id, error_msg)
            raise

    def _call_provider(
        self,
        prompt: str,
        provider_name: str,
        params: dict[str, Any] | None = None,
        reference_images: list[str] | None = None,
        reference_image: str = "",
        prev_shot_last_frame: str = "",
        task_context: GenerateTaskContext | None = None,
    ) -> tuple[str, dict[str, Any], int | None]:
        provider = self.get_provider(provider_name)
        params = (params or {}).copy()
        prev_last = prev_shot_last_frame or params.pop("first_frame_path", None)

        if reference_images:
            main_ref = reference_images[0]
            if len(reference_images) > 1:
                params["reference_media"] = [
                    {"path": p, "type": "reference_image"}
                    for p in reference_images[1:]
                ]
            if prev_last:
                params["first_frame_path"] = prev_last
            provider_task_id, request_details, child_task_id = provider.r2v(
                prompt=prompt,
                reference_path=main_ref,
                params=params,
                task_context=task_context,
            )
            logger.info(f"使用参考生视频 (r2v)：{len(reference_images)} 张参考图")
        elif prev_last:
            provider_task_id, request_details, child_task_id = provider.p2v(
                prompt=prompt,
                image_path=prev_last,
                params=params,
                task_context=task_context,
            )
            logger.info(f"使用图生视频 (p2v)：上一镜尾帧={prev_last}")
        elif reference_image:
            provider_task_id, request_details, child_task_id = provider.r2v(
                prompt=prompt,
                reference_path=reference_image,
                params=params,
                task_context=task_context,
            )
            logger.info(f"使用参考生视频 (r2v)：reference_image={reference_image}")
        else:
            provider_task_id, request_details, child_task_id = provider.t2v(
                prompt=prompt,
                params=params,
                task_context=task_context,
            )
            logger.info("使用文生视频 (t2v)")

        return provider_task_id, request_details, child_task_id

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
        prev_shot_last_frame: str = "",
    ) -> str:
        request = VideoGenerationRequest(
            scene=VideoScene.SHOT_VIDEO,
            storyboard_id=storyboard.id,
            local_path=local_path,
            provider_name=provider_name,
            project_id=project_id,
            project_name=project_name,
            scene_id=scene.id if scene else storyboard.scene_id,
            prev_shot_id=prev_shot.id if prev_shot else None,
            next_shot_id=next_shot.id if next_shot else None,
            scene_number=storyboard.scene_number,
            shot_number=storyboard.shot_number,
            reference_images=list(reference_images or []),
            reference_images_info=list(reference_images_info or []),
            visual_style=visual_style,
            params=dict(params or {}),
            prev_shot_last_frame=prev_shot_last_frame,
            clean_prompt=clean_prompt,
        )
        return self.start_shot_video(request, wait_submit=True)

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
        scene_number: int = 0,
        shot_number: int = 0,
        prev_shot_last_frame: str = "",
    ) -> str:
        request = VideoGenerationRequest(
            scene=VideoScene.SHOT_VIDEO,
            storyboard_id=storyboard_id,
            local_path=local_path,
            provider_name=provider_name,
            project_id=project_id,
            project_name=project_name,
            scene_number=scene_number,
            shot_number=shot_number,
            reference_images=list(reference_images or []),
            reference_image=reference_image,
            params=dict(params or {}),
            prev_shot_last_frame=prev_shot_last_frame,
            clean_prompt=False,
        )
        pending_id, task_id = self._create_pending_task(request)
        get_video_signal_emitter().take_created.emit()

        task_context = GenerateTaskContext(
            session_manager=self._sm,
            parent_ids=str(task_id),
            caller_type=GenerateTaskCallerType.STORYBOARD,
            caller_id=str(storyboard_id),
            project_id=project_id,
            project_name=project_name,
            module="storyboard",
            context="视频生成提交",
            local_path=local_path,
        )
        provider_task_id, _request_details, _child_task_id = self._call_provider(
            prompt=flatten_prompt_text(prompt),
            provider_name=provider_name,
            params=params,
            reference_images=reference_images,
            reference_image=reference_image,
            prev_shot_last_frame=prev_shot_last_frame,
            task_context=task_context,
        )

        return provider_task_id
