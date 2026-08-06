from __future__ import annotations

import os
import shutil
import time
import uuid
from loguru import logger
from typing import Any, TYPE_CHECKING

from PySide6.QtCore import QObject, Signal

from service.background.task_base import BackgroundTask, TaskType
from models.enums import MessageStatus, TaskStatus
from storage.session_manager import SessionManager
from storage.repositories.generate_task_repository import GenerateTaskRepository
from storage.repositories.oss_cache_repository import OSSFileCacheRepository
from utils import paths
from utils.path_converter import to_relative_path

if TYPE_CHECKING:
    from providers.video_base import VideoProvider


class VideoTaskPollingTask(BackgroundTask):

    def __init__(
        self,
        session_manager: SessionManager,
        provider_registry: dict[str, type[VideoProvider]],
        workspace_root: str,
        poll_interval: float = 20.0,
        idle_check_interval: float = 60.0,
        max_polls_per_task: int = 150,
    ) -> None:
        super().__init__(TaskType.PERIODIC, "video_task_polling")

        self._signal_emitter = _SignalEmitter()

        self._sm = session_manager
        self._provider_registry = provider_registry
        self._providers: dict[str, VideoProvider] = {}
        self._workspace_root = workspace_root
        self._cache_dir = paths.cache_dir(workspace_root)

        self._poll_interval = poll_interval
        self._idle_check_interval = idle_check_interval
        self._max_polls_per_task = max_polls_per_task

        self._task_poll_count: dict[int, int] = {}

        self._last_cleanup_time = time.time()
        self._cleanup_interval = 3600.0

        self._last_check_time = time.time()

        self._media_service: Any = None
        self._config_manager: Any = None

        self.enable()

    @property
    def signal_emitter(self) -> QObject:
        return self._signal_emitter

    def set_media_service(self, media_service: Any) -> None:
        self._media_service = media_service

    def set_config_manager(self, config_manager: Any) -> None:
        self._config_manager = config_manager

    def get_provider(self, name: str) -> VideoProvider:
        if name in self._providers:
            return self._providers[name]

        if self._config_manager is None:
            raise RuntimeError("ConfigManager 未注入")

        cfg = self._config_manager.get_provider_config(name=name, provider_type="video")
        if cfg is None:
            raise KeyError(f"未配置的 Provider：{name}")

        cls = self._provider_registry.get(name)
        if cls is None:
            raise KeyError(f"未注册的 Provider：{name}")

        provider = cls(cfg)

        if hasattr(provider, "set_session_manager"):
            provider.set_session_manager(self._sm)

        self._providers[name] = provider
        return provider

    def execute(self) -> None:
        try:
            now = time.time()
            if now - self._last_cleanup_time >= self._cleanup_interval:
                self._cleanup_expired_oss_caches()
                self._last_cleanup_time = now

            task_repo = self._sm.get_repo(repo_class=GenerateTaskRepository)
            tasks = task_repo.list_active_tasks()

            if not tasks:
                self.interruptible_sleep(self._idle_check_interval)
                return

            for task_info in tasks:
                self._process_task(task_info)

            self._last_check_time = now

        except Exception as e:
            logger.exception(f"轮询任务执行异常：{e}")

    def _cleanup_expired_oss_caches(self) -> None:
        try:
            oss_cache_repo = self._sm.get_repo(repo_class=OSSFileCacheRepository)
            self._sm.begin_write()
            try:
                count = oss_cache_repo.delete_expired_caches()
                self._sm.commit_write()
                if count > 0:
                    logger.info(f"已清理 {count} 条过期 OSS 缓存记录")
            except Exception:
                self._sm.rollback_write()
                raise
        except Exception as e:
            logger.warning(f"清理过期 OSS 缓存失败: {e}")

    def _process_task(self, task_info: dict[str, Any]) -> None:
        internal_task_id = task_info["id"]
        provider_task_id = task_info["provider_task_id"]
        provider_name = task_info["provider_name"]
        model_name = task_info["model_name"]
        storyboard_id = task_info.get("storyboard_id", 0)

        poll_count = self._task_poll_count.get(internal_task_id, 0)
        if poll_count >= self._max_polls_per_task:
            error_msg = f"轮询超时（已查询 {poll_count} 次，任务仍未完成）"
            logger.warning(f"任务超时 internal_id={internal_task_id}")
            self._handle_task_failed(provider_task_id, internal_task_id, error_msg)
            return

        write_lock_acquired = False

        try:
            provider = self.get_provider(provider_name)
            result = provider.check_status(task_id=provider_task_id)
            self._task_poll_count[internal_task_id] = poll_count + 1

            current_status = task_info["status"]
            status_changed = current_status != result.status.value

            if status_changed:
                task_repo = self._sm.get_repo(repo_class=GenerateTaskRepository)
                self._sm.begin_write()
                write_lock_acquired = True
                try:
                    task_repo.update_status(internal_task_id, result.status.value, video_url=result.video_url or "")
                    self._sm.commit_write()
                    write_lock_acquired = False
                except Exception:
                    self._sm.rollback_write()
                    write_lock_acquired = False
                    raise

                self._signal_emitter.status_changed.emit(provider_task_id, result.status.value)

            if result.status == TaskStatus.SUCCEEDED:
                if not result.video_url:
                    raise RuntimeError("任务成功但未返回视频地址")
                self._download_and_finish(
                    provider=provider,
                    internal_task_id=internal_task_id,
                    provider_task_id=provider_task_id,
                    video_url=result.video_url,
                    model_name=model_name,
                    save_path=task_info.get("save_path", ""),
                    storyboard_id=storyboard_id,
                )
            elif result.status == TaskStatus.FAILED:
                error_msg = result.error_message or "未知原因"
                self._handle_task_failed(provider_task_id, internal_task_id, f"任务失败：{error_msg}")
                self._signal_emitter.task_failed.emit(provider_task_id, f"任务失败：{error_msg}")

        except Exception as e:
            if write_lock_acquired:
                try:
                    self._sm.rollback_write()
                except Exception as rollback_error:
                    logger.error(f"回滚写锁失败: {rollback_error}")

            logger.warning(f"轮询异常 internal_id={internal_task_id}（第 {poll_count + 1} 次）：{e}")
            self._task_poll_count[internal_task_id] = poll_count + 1

    def _mark_task_completed(self, internal_task_id: int) -> None:
        task_repo = self._sm.get_repo(repo_class=GenerateTaskRepository)
        self._sm.begin_write()
        try:
            task_repo.mark_completed(task_id=internal_task_id)
            self._sm.commit_write()
        except Exception:
            self._sm.rollback_write()
            raise
        self._task_poll_count.pop(internal_task_id, None)

    def _handle_task_failed(self, provider_task_id: str, internal_task_id: int, error: str) -> None:
        self._mark_task_completed(internal_task_id)
        self._signal_emitter.task_failed.emit(provider_task_id, error)

    def _download_and_finish(
        self,
        provider: VideoProvider,
        internal_task_id: int,
        provider_task_id: str,
        video_url: str,
        model_name: str,
        save_path: str = "",
        storyboard_id: int = 0,
    ) -> None:
        try:
            workspace = paths.workspace_dir(self._workspace_root)
            if save_path:
                save_path = os.path.join(workspace, save_path)
            else:
                import time
                target_dir = paths.workspace_dir(self._workspace_root)
                stamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"{stamp}_{model_name}_video.mp4"
                save_path = os.path.join(target_dir, filename)

            os.makedirs(self._cache_dir, exist_ok=True)
            tmp_path = os.path.join(self._cache_dir, f"{uuid.uuid4().hex}.mp4.part")

            provider.download(video_url=video_url, save_path=tmp_path, progress_callback=None)

            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            shutil.move(src=tmp_path, dst=save_path)

            relative_save_path = to_relative_path(save_path, self._workspace_root)

            if self._media_service:
                try:
                    self._media_service.register_task_result(
                        provider_task_id, save_path, "", storyboard_id=storyboard_id
                    )
                except Exception as e:
                    logger.warning(f"素材自动入库失败：{e}")

            self._mark_task_completed(internal_task_id)
            logger.info(f"任务完成 internal_id={internal_task_id} local_path={save_path}")

            self._signal_emitter.task_finished.emit(provider_task_id, save_path, storyboard_id)

        except Exception as e:
            logger.exception(f"下载失败 internal_id={internal_task_id}")
            self._handle_task_failed(provider_task_id, internal_task_id, f"下载失败：{e}")

    def should_continue(self) -> bool:
        return True

    def get_interval(self) -> float:
        return self._poll_interval


class _SignalEmitter(QObject):

    status_changed = Signal(str, str)
    download_progress = Signal(str, int, int)
    task_finished = Signal(str, str, int)
    task_failed = Signal(str, str)
