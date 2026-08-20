from __future__ import annotations

import json
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


def _resolve_task_local_path(parent_info: dict[str, Any] | None, task_info: dict[str, Any]) -> str:
    if parent_info:
        local_path = parent_info.get("local_path", "")
        if not local_path:
            try:
                params = json.loads(parent_info.get("request_params", "{}"))
                local_path = params.get("local_path", "")
            except (json.JSONDecodeError, TypeError):
                local_path = ""
        if local_path:
            return local_path
    return task_info.get("local_path", "")


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

    def invalidate_provider_cache(self) -> None:
        if self._providers:
            logger.info("清空 Provider 缓存：video_polling")
        self._providers.clear()

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
            from models.enums import GenerateTaskType
            tasks = task_repo.list_active_child_tasks(task_type=GenerateTaskType.VIDEO)

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
        caller_type = task_info.get("caller_type")
        caller_id = task_info.get("caller_id", "")

        task_repo = self._sm.get_repo(repo_class=GenerateTaskRepository)
        parent_task_id = GenerateTaskRepository.get_parent_task_id(task_info.get("parent_ids", ""))
        parent_info = task_repo.get_by_id(parent_task_id) if parent_task_id else None
        signal_provider_task_id = (
            parent_info["provider_task_id"] if parent_info else provider_task_id
        )
        local_path = _resolve_task_local_path(parent_info, task_info)

        poll_count = self._task_poll_count.get(internal_task_id, 0)
        if poll_count >= self._max_polls_per_task:
            error_msg = f"轮询超时（已查询 {poll_count} 次，任务仍未完成）"
            logger.warning(f"任务超时 internal_id={internal_task_id}")
            self._handle_task_failed(
                signal_provider_task_id,
                internal_task_id,
                error_msg,
                parent_task_id=parent_task_id,
            )
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
                    task_repo.update_status(internal_task_id, result.status.value, remote_url=result.video_url or "")
                    self._sm.commit_write()
                    write_lock_acquired = False
                except Exception:
                    self._sm.rollback_write()
                    write_lock_acquired = False
                    raise

                self._signal_emitter.status_changed.emit(signal_provider_task_id, result.status.value)

            if result.status == TaskStatus.SUCCEEDED:
                if not result.video_url:
                    raise RuntimeError("任务成功但未返回视频地址")
                self._download_and_finish(
                    provider=provider,
                    internal_task_id=internal_task_id,
                    provider_task_id=signal_provider_task_id,
                    remote_url=result.video_url,
                    model_name=model_name,
                    local_path=local_path,
                    caller_type=caller_type,
                    caller_id=caller_id,
                    parent_task_id=parent_task_id,
                )
            elif result.status == TaskStatus.FAILED:
                error_msg = result.error_message or "未知原因"
                self._handle_task_failed(
                    signal_provider_task_id,
                    internal_task_id,
                    f"任务失败：{error_msg}",
                    parent_task_id=parent_task_id,
                )

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

    def _sync_parent_task(
        self,
        parent_task_id: int | None,
        status: str,
        error_message: str = "",
        *,
        mark_completed: bool = False,
    ) -> None:
        if not parent_task_id:
            return
        task_repo = self._sm.get_repo(repo_class=GenerateTaskRepository)
        self._sm.begin_write()
        try:
            task_repo.update_status(
                parent_task_id,
                status,
                error_message=error_message,
            )
            if mark_completed:
                task_repo.mark_completed(task_id=parent_task_id)
            self._sm.commit_write()
        except Exception:
            self._sm.rollback_write()
            raise

    def _handle_task_failed(
        self,
        provider_task_id: str,
        internal_task_id: int,
        error: str,
        parent_task_id: int | None = None,
    ) -> None:
        task_repo = self._sm.get_repo(repo_class=GenerateTaskRepository)
        self._sm.begin_write()
        try:
            task_repo.update_status(internal_task_id, "failed", error_message=error)
            task_repo.mark_completed(task_id=internal_task_id)
            self._sm.commit_write()
        except Exception:
            self._sm.rollback_write()
            raise
        self._sync_parent_task(
            parent_task_id,
            "failed",
            error_message=error,
            mark_completed=True,
        )
        self._task_poll_count.pop(internal_task_id, None)
        self._signal_emitter.task_failed.emit(provider_task_id, error)

    def _download_and_finish(
        self,
        provider: VideoProvider,
        internal_task_id: int,
        provider_task_id: str,
        remote_url: str,
        model_name: str,
        local_path: str = "",
        caller_type: str | None = None,
        caller_id: str = "",
        parent_task_id: int | None = None,
    ) -> None:
        try:
            workspace = paths.workspace_dir(self._workspace_root)
            if local_path:
                absolute_path = os.path.join(workspace, local_path)
            else:
                import time
                target_dir = paths.workspace_dir(self._workspace_root)
                stamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"{stamp}_{model_name}_video.mp4"
                absolute_path = os.path.join(target_dir, filename)

            os.makedirs(self._cache_dir, exist_ok=True)
            tmp_path = os.path.join(self._cache_dir, f"{uuid.uuid4().hex}.mp4.part")

            provider.download(video_url=remote_url, save_path=tmp_path, progress_callback=None)

            os.makedirs(os.path.dirname(absolute_path), exist_ok=True)
            shutil.move(src=tmp_path, dst=absolute_path)

            relative_save_path = to_relative_path(absolute_path, self._workspace_root)

            if self._media_service:
                try:
                    # 根据 caller_type 判断是否传递 storyboard_id
                    storyboard_id = int(caller_id) if caller_type == "storyboard" and caller_id else 0
                    self._media_service.register_task_result(
                        provider_task_id, absolute_path, "", storyboard_id=storyboard_id
                    )
                except Exception as e:
                    logger.warning(f"素材自动入库失败：{e}")

            task_repo = self._sm.get_repo(repo_class=GenerateTaskRepository)
            self._sm.begin_write()
            try:
                task_repo.update_status(internal_task_id, "succeeded", remote_url=remote_url)
                task_repo.mark_completed(task_id=internal_task_id)
                self._sm.commit_write()
            except Exception:
                self._sm.rollback_write()
                raise
            self._sync_parent_task(
                parent_task_id,
                "succeeded",
                mark_completed=True,
            )
            self._task_poll_count.pop(internal_task_id, None)
            logger.info(f"任务完成 internal_id={internal_task_id} local_path={absolute_path}")

            # 根据 caller_type 发送信号
            storyboard_id = int(caller_id) if caller_type == "storyboard" and caller_id else 0
            self._signal_emitter.task_finished.emit(provider_task_id, absolute_path, storyboard_id)

        except Exception as e:
            logger.exception(f"下载失败 internal_id={internal_task_id}")
            self._handle_task_failed(
                provider_task_id,
                internal_task_id,
                f"下载失败：{e}",
                parent_task_id=parent_task_id,
            )

    def should_continue(self) -> bool:
        return True

    def get_interval(self) -> float:
        return self._poll_interval


class _SignalEmitter(QObject):

    status_changed = Signal(str, str)
    download_progress = Signal(str, int, int)
    task_finished = Signal(str, str, int)
    task_failed = Signal(str, str)
