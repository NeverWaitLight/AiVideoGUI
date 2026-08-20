"""图片生成后台任务：在 QThread 中执行完整流水线"""
from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger
from PySide6.QtCore import QObject, QThread, Signal

from config.manager import ConfigManager
from providers.dashscope_image import DashScopeImageProvider
from providers.image_base import ImageProvider
from storage.session_manager import SessionManager
from storage.repositories.generate_task_repository import GenerateTaskRepository

if TYPE_CHECKING:
    from service.image_service import ImageService

_PROVIDER_REGISTRY: dict[str, type[ImageProvider]] = {
    "dashscope": DashScopeImageProvider,
    "dashscope_image": DashScopeImageProvider,
}


class _ImageSignalEmitter(QObject):
    task_started = Signal(str, str, str)  # provider_task_id, caller_type, caller_id
    task_progress = Signal(str, str)  # provider_task_id, message
    task_finished = Signal(str, str, str, str)  # provider_task_id, caller_type, caller_id, relative_path
    task_failed = Signal(str, str, str, str)  # provider_task_id, caller_type, caller_id, error_message


_signal_emitter = _ImageSignalEmitter()


def get_image_signal_emitter() -> _ImageSignalEmitter:
    return _signal_emitter


def _mark_task_failed(
    session_manager: SessionManager,
    provider_task_id: str,
    error_msg: str,
) -> None:
    try:
        task_repo = session_manager.get_repo(repo_class=GenerateTaskRepository)
        task_info = task_repo.get_by_provider_task_id(provider_task_id)
        if not task_info:
            return
        if task_info.get("completed"):
            return
        session_manager.begin_write()
        try:
            task_repo.update_status(task_info["id"], "failed", error_message=error_msg)
            task_repo.mark_completed(task_info["id"])
            session_manager.commit_write()
        except Exception:
            session_manager.rollback_write()
            raise
    except Exception as db_error:
        logger.error(f"更新任务失败状态时出错：{db_error}")


class ImageGenerationWorker(QThread):
    finished_with_path = Signal(str, str)  # provider_task_id, relative_path
    failed_with_error = Signal(str, str)  # provider_task_id, error_message

    def __init__(self, image_service: ImageService, provider_task_id: str, parent=None):
        super().__init__(parent)
        self._image_service = image_service
        self._provider_task_id = provider_task_id

    def run(self):
        try:
            relative_path = self._image_service.execute_pipeline(self._provider_task_id)
            self.finished_with_path.emit(self._provider_task_id, relative_path)
        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            self.failed_with_error.emit(self._provider_task_id, error_msg)


class ImageGenerationCoordinator(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._active_workers: dict[str, ImageGenerationWorker] = {}
        self._active_callers: set[str] = set()

    def is_caller_active(self, caller_key: str) -> bool:
        return caller_key in self._active_callers

    def start(self, image_service: ImageService, provider_task_id: str, caller_key: str) -> None:
        if caller_key in self._active_callers:
            raise RuntimeError("该对象已有图片生成任务进行中")

        worker = ImageGenerationWorker(image_service, provider_task_id, parent=self)
        self._active_workers[provider_task_id] = worker
        self._active_callers.add(caller_key)

        def _cleanup(_pid: str = provider_task_id, _key: str = caller_key) -> None:
            self._active_workers.pop(_pid, None)
            self._active_callers.discard(_key)
            worker.deleteLater()

        worker.finished_with_path.connect(lambda _pid, _path: _cleanup())
        worker.failed_with_error.connect(lambda _pid, _err: _cleanup())
        worker.start()


class BatchImageGenerationWorker(QThread):
    progress_update = Signal(int, str, str)
    shot_design_started = Signal(int)
    shot_design_done = Signal(int, str)
    shot_design_failed = Signal(int)
    finished = Signal(int, int)
    failed = Signal(str)

    def __init__(self, image_service: ImageService, shot_list: list[dict], parent=None):
        super().__init__(parent)
        self._image_service = image_service
        self._shot_list = shot_list

    def run(self):
        success_count = 0
        total = len(self._shot_list)

        shot_size_map = {
            "extreme_close_up": "特写",
            "close_up": "近景",
            "medium_shot": "中景",
            "full_shot": "全景",
            "long_shot": "远景",
            "extreme_long_shot": "大远景",
        }

        for idx, shot_data in enumerate(self._shot_list, start=1):
            storyboard_id = shot_data["storyboard_id"]
            self.shot_design_started.emit(storyboard_id)
            try:
                project_id = shot_data["project_id"]
                scene_number = shot_data["scene_number"]
                shot_number = shot_data["shot_number"]

                self.progress_update.emit(
                    idx - 1,
                    f"正在生成 {scene_number}-{shot_number} 镜设计图...",
                    f"({idx}/{total})",
                )

                shot_size = shot_data["shot_size"]
                shot_size_text = (
                    shot_size_map.get(shot_size.value, "中景")
                    if hasattr(shot_size, "value")
                    else shot_size_map.get(shot_size, "中景")
                )

                provider_task_id = self._image_service.start_storyboard_design_image(
                    content=shot_data["content"],
                    storyboard_id=storyboard_id,
                    project_id=project_id,
                    scene_number=scene_number,
                    shot_number=shot_number,
                    shot_size=shot_size_text,
                    camera_movement=shot_data.get("camera_movement", ""),
                    notes=shot_data.get("notes", ""),
                    character_info=shot_data.get("character_info", ""),
                    visual_style=shot_data.get("visual_style", ""),
                    project_name=shot_data.get("project_name"),
                    aspect_ratio=shot_data.get("aspect_ratio", ""),
                    wait=True,
                )
                task_repo = self._image_service._sm.get_repo(repo_class=GenerateTaskRepository)
                task_info = task_repo.get_by_provider_task_id(provider_task_id)
                relative_path = task_info.get("local_path", "") if task_info else ""

                success_count += 1
                self.shot_design_done.emit(storyboard_id, relative_path)
                self.progress_update.emit(
                    idx,
                    f"完成 {scene_number}-{shot_number}",
                    f"({idx}/{total})",
                )
            except Exception:
                self.shot_design_failed.emit(storyboard_id)
                self.progress_update.emit(idx, "生成失败", f"({idx}/{total})")

        self.finished.emit(success_count, total)


def _get_image_provider(
    config_manager: ConfigManager,
    provider_name: str,
    cache: dict[str, ImageProvider],
) -> ImageProvider:
    if provider_name in cache:
        return cache[provider_name]

    provider_cfg = config_manager.resolve_config_for_type(name=provider_name, provider_type="image")
    if not provider_cfg or not provider_cfg.api_key:
        raise RuntimeError(f"未配置图片生成供应商 {provider_name} 的 API Key")

    cls = _PROVIDER_REGISTRY.get(provider_name)
    if not cls:
        raise RuntimeError(f"未知的图片供应商：{provider_name}")

    provider = cls(provider_cfg)
    cache[provider_name] = provider
    return provider


def emit_task_failed(
    session_manager: SessionManager,
    provider_task_id: str,
    caller_type: str,
    caller_id: str,
    error_msg: str,
) -> None:
    _mark_task_failed(session_manager, provider_task_id, error_msg)
    _signal_emitter.task_failed.emit(provider_task_id, caller_type, caller_id, error_msg)
