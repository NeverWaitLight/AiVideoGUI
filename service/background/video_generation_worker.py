"""视频生成后台任务：在 QThread 中执行提交阶段流水线"""
from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger
from PySide6.QtCore import QObject, QThread, Signal

from storage.session_manager import SessionManager
from storage.repositories.generate_task_repository import GenerateTaskRepository

if TYPE_CHECKING:
    from service.video_service import VideoService


class _VideoSignalEmitter(QObject):
    task_started = Signal(str, str, str)  # provider_task_id, caller_type, caller_id
    task_progress = Signal(str, str)  # provider_task_id, message
    submit_finished = Signal(str, str)  # pending_provider_task_id, final_provider_task_id
    take_created = Signal()
    video_generation_started = Signal(str)  # storyboard_id
    video_generation_finished = Signal(str)  # storyboard_id
    video_generation_failed = Signal(str, str)  # storyboard_id, error_message
    task_failed = Signal(str, str, str, str)  # provider_task_id, caller_type, caller_id, error


_signal_emitter = _VideoSignalEmitter()


def get_video_signal_emitter() -> _VideoSignalEmitter:
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
        logger.error(f"更新视频任务失败状态时出错：{db_error}")


class VideoGenerationWorker(QThread):
    finished_with_provider_id = Signal(str, str)  # pending_id, final_provider_task_id
    failed_with_error = Signal(str, str)  # pending_provider_task_id, error_message

    def __init__(self, video_service: VideoService, pending_provider_task_id: str, parent=None):
        super().__init__(parent)
        self._video_service = video_service
        self._pending_provider_task_id = pending_provider_task_id

    def run(self):
        try:
            final_id = self._video_service.execute_submit_pipeline(self._pending_provider_task_id)
            self.finished_with_provider_id.emit(self._pending_provider_task_id, final_id)
        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            self.failed_with_error.emit(self._pending_provider_task_id, error_msg)


class VideoGenerationCoordinator(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._active_workers: dict[str, VideoGenerationWorker] = {}
        self._active_callers: set[str] = set()

    def is_caller_active(self, caller_key: str) -> bool:
        return caller_key in self._active_callers

    def start(self, video_service: VideoService, pending_provider_task_id: str, caller_key: str) -> None:
        if caller_key in self._active_callers:
            raise RuntimeError("该分镜已有视频生成任务进行中")

        worker = VideoGenerationWorker(video_service, pending_provider_task_id, parent=self)
        self._active_workers[pending_provider_task_id] = worker
        self._active_callers.add(caller_key)

        def _cleanup(_pid: str = pending_provider_task_id, _key: str = caller_key) -> None:
            self._active_workers.pop(_pid, None)
            self._active_callers.discard(_key)
            worker.deleteLater()

        worker.finished_with_provider_id.connect(lambda _pending, _final: _cleanup())
        worker.failed_with_error.connect(lambda _pid, _err: _cleanup())
        worker.start()


def emit_video_task_failed(
    session_manager: SessionManager,
    provider_task_id: str,
    caller_type: str,
    caller_id: str,
    error_msg: str,
) -> None:
    _mark_task_failed(session_manager, provider_task_id, error_msg)
    _signal_emitter.task_failed.emit(provider_task_id, caller_type, caller_id, error_msg)
