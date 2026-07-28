"""全局任务轮询服务：独立后台线程，按照 active_tasks 表驱动轮询策略。"""

from __future__ import annotations

from loguru import logger
import os
import shutil
import time
import uuid
from typing import Any

from PySide6.QtCore import QObject, QThread, Signal

from config.manager import ConfigManager
from models.enums import MessageStatus, TaskStatus
from providers.video_base import VideoProvider
from storage.session_manager import SessionManager
from storage.repositories.active_task_repository import ActiveTaskRepository
from storage.repositories.message_repository import MessageRepository
from storage.repositories.oss_cache_repository import OSSFileCacheRepository
from utils import paths

class TaskPollingService(QObject):
    """全局任务轮询服务：应用启动时运行，根据 active_tasks 表自动启停。"""

    status_changed = Signal(str, str)
    download_progress = Signal(str, int, int)
    task_finished = Signal(str, str, int)
    task_failed = Signal(str, str)

    def __init__(
        self,
        session_manager: SessionManager,
        config: ConfigManager,
        workspace_root: str,
        provider_registry: dict[str, type[VideoProvider]],
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._session_manager = session_manager
        self._config = config
        self._root = workspace_root
        self._cache_dir = paths.cache_dir(workspace_root)
        self._provider_registry = provider_registry
        self._providers: dict[str, VideoProvider] = {}
        self._worker: _PollingWorker | None = None
        self._media_service: Any = None

        # 轮询策略配置
        self.poll_interval = 10.0  # 任务状态检查间隔（秒）
        self.idle_check_interval = 60.0  # 空闲时检查表是否有新任务的间隔（秒）
        self.max_polls_per_task = 150  # 单个任务最大轮询次数

    def set_media_service(self, media_service: Any) -> None:
        """注入素材库服务，用于任务完成后自动入库。"""
        self._media_service = media_service

    def get_provider(self, name: str) -> VideoProvider:
        """获取或创建 Provider 实例。"""
        if name in self._providers:
            return self._providers[name]
        cfg = self._config.get_provider(name)
        if cfg is None:
            raise KeyError(f"未配置的 Provider：{name}")
        cls = self._provider_registry.get(name)
        if cls is None:
            raise KeyError(f"未注册的 Provider：{name}")
        provider = cls(cfg)

        # 注入 SessionManager（用于 OSS 缓存）
        if hasattr(provider, "set_session_manager"):
            provider.set_session_manager(self._session_manager)

        self._providers[name] = provider
        return provider

    def start(self) -> None:
        """启动全局轮询服务。"""
        if self._worker is not None:
            logger.warning("轮询服务已在运行")
            return
        self._worker = _PollingWorker(
            session_manager=self._session_manager,
            service=self,
            poll_interval=self.poll_interval,
            idle_check_interval=self.idle_check_interval,
            max_polls_per_task=self.max_polls_per_task,
            workspace_root=self._root,
            cache_dir=self._cache_dir,
        )
        self._worker.status_changed.connect(self._on_status_changed)
        self._worker.download_progress.connect(self._on_download_progress)
        self._worker.task_finished.connect(self._on_task_finished)
        self._worker.task_failed.connect(self._on_task_failed)
        self._worker.start()
        logger.info("任务轮询服务已启动")

    def shutdown(self) -> None:
        """停止轮询服务。"""
        if self._worker is None:
            return
        self._worker.stop()
        self._worker.wait(5000)
        self._worker = None
        logger.info("任务轮询服务已停止")

    # ---------- Worker 信号处理 ----------

    def _on_status_changed(self, message_id: str, status: str) -> None:
        _TASK_TO_MSG_STATUS = {
            "pending": MessageStatus.GENERATING,
            "running": MessageStatus.GENERATING,
            "succeeded": MessageStatus.COMPLETED,
            "failed": MessageStatus.FAILED,
        }
        msg_status = _TASK_TO_MSG_STATUS.get(status)
        if msg_status is not None:
            msg_repo = self._session_manager.get_repo(MessageRepository)
            self._session_manager.begin_write()
            try:
                msg_repo.update_status(message_id, msg_status)
                self._session_manager.commit_write()
            except Exception:
                self._session_manager.rollback_write()
                raise
        self.status_changed.emit(message_id, status)

    def _on_download_progress(self, message_id: str, downloaded: int, total: int) -> None:
        self.download_progress.emit(message_id, downloaded, total)

    def _on_task_finished(self, message_id: str, local_path: str, storyboard_id: int = 0) -> None:
        msg_repo = self._session_manager.get_repo(MessageRepository)
        msg = msg_repo.get_by_id(message_id)

        self._session_manager.begin_write()
        try:
            msg_repo.update_status(message_id, MessageStatus.COMPLETED, local_path=local_path)
            self._session_manager.commit_write()
        except Exception:
            self._session_manager.rollback_write()
            raise

        if msg and self._media_service:
            try:
                self._media_service.register_task_result(
                    message_id, local_path, msg.conversation_id, storyboard_id=storyboard_id
                )
            except Exception as e:
                logger.warning(f"素材自动入库失败：{e}")
        self.task_finished.emit(message_id, local_path, storyboard_id)

    def _on_task_failed(self, message_id: str, error: str) -> None:
        msg_repo = self._session_manager.get_repo(MessageRepository)
        self._session_manager.begin_write()
        try:
            msg_repo.update_status(message_id, MessageStatus.FAILED, error_message=error)
            self._session_manager.commit_write()
        except Exception:
            self._session_manager.rollback_write()
            raise
        self.task_failed.emit(message_id, error)

class _PollingWorker(QThread):
    """后台轮询线程：周期性扫描 active_tasks 表，按任务创建时间执行轮询策略。"""

    status_changed = Signal(str, str)
    download_progress = Signal(str, int, int)
    task_finished = Signal(str, str, int)
    task_failed = Signal(str, str)

    def __init__(
        self,
        session_manager: SessionManager,
        service: TaskPollingService,
        poll_interval: float,
        idle_check_interval: float,
        max_polls_per_task: int,
        workspace_root: str,
        cache_dir: str,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._session_manager = session_manager
        self._service = service
        self._poll_interval = poll_interval
        self._idle_check_interval = idle_check_interval
        self._max_polls_per_task = max_polls_per_task
        self._root = workspace_root
        self._cache_dir = cache_dir
        self._stopped = False
        self._task_poll_count: dict[int, int] = {}  # internal task id -> 已轮询次数

    def stop(self) -> None:
        self._stopped = True

    def _interruptible_sleep(self, seconds: float) -> bool:
        """可中断 sleep，每秒检查 _stopped 标志。返回 True 表示被中断。"""
        elapsed = 0.0
        while elapsed < seconds:
            if self._stopped:
                return True
            time.sleep(min(1.0, seconds - elapsed))
            elapsed += 1.0
        return False

    def run(self) -> None:
        """主循环：检查 active_tasks 表，处理待轮询任务。"""
        logger.info("轮询线程进入主循环")
        last_cleanup_time = time.time()
        cleanup_interval = 3600.0  # 每小时清理一次过期 OSS 缓存

        while not self._stopped:
            try:
                # 定期清理过期 OSS 缓存
                now = time.time()
                if now - last_cleanup_time >= cleanup_interval:
                    self._cleanup_expired_oss_caches()
                    last_cleanup_time = now

                task_repo = self._session_manager.get_repo(ActiveTaskRepository)
                tasks = task_repo.list_active_tasks()
                if not tasks:
                    # 表空，进入空闲模式
                    if self._interruptible_sleep(self._idle_check_interval):
                        break
                    continue

                # 处理每个活跃任务
                for task_info in tasks:
                    if self._stopped:
                        break
                    self._process_task(task_info)

                # 正常轮询间隔
                if self._interruptible_sleep(self._poll_interval):
                    break

            except Exception as e:
                logger.exception(f"轮询线程异常：{e}")
                if self._interruptible_sleep(self._poll_interval):
                    break

        logger.info("轮询线程已退出")

    def _cleanup_expired_oss_caches(self) -> None:
        """清理过期的 OSS 缓存记录（异步执行，不阻塞主循环）"""
        try:
            oss_cache_repo = self._session_manager.get_repo(OSSFileCacheRepository)
            self._session_manager.begin_write()
            try:
                count = oss_cache_repo.delete_expired_caches()
                self._session_manager.commit_write()
                if count > 0:
                    logger.info(f"已清理 {count} 条过期 OSS 缓存记录")
            except Exception:
                self._session_manager.rollback_write()
                raise
        except Exception as e:
            logger.warning(f"清理过期 OSS 缓存失败: {e}")

    def _process_task(self, task_info: dict[str, Any]) -> None:
        """处理单个任务：检查是否需要轮询、执行状态查询、下载视频。"""
        internal_task_id = task_info["id"]
        provider_task_id = task_info["provider_task_id"]
        message_id = task_info["message_id"]
        provider_name = task_info["provider_name"]
        model_name = task_info["model_name"]

        # 检查消息状态
        msg_repo = self._session_manager.get_repo(MessageRepository)
        msg = msg_repo.get_by_id(message_id)
        if not msg:
            logger.warning(f"任务关联消息不存在，标记完成 internal_id={internal_task_id} provider_task={provider_task_id}")
            task_repo = self._session_manager.get_repo(ActiveTaskRepository)
            self._session_manager.begin_write()
            try:
                task_repo.mark_completed(internal_task_id)
                self._session_manager.commit_write()
            except Exception:
                self._session_manager.rollback_write()
                raise
            self._task_poll_count.pop(internal_task_id, None)
            return

        # 消息已是终态，标记任务完成
        if msg.status in (MessageStatus.COMPLETED, MessageStatus.FAILED):
            task_repo = self._session_manager.get_repo(ActiveTaskRepository)
            self._session_manager.begin_write()
            try:
                task_repo.mark_completed(internal_task_id)
                self._session_manager.commit_write()
            except Exception:
                self._session_manager.rollback_write()
                raise
            self._task_poll_count.pop(internal_task_id, None)
            return

        # 检查是否超过最大轮询次数
        poll_count = self._task_poll_count.get(internal_task_id, 0)
        if poll_count >= self._max_polls_per_task:
            error_msg = f"轮询超时（已查询 {poll_count} 次，任务仍未完成）"
            logger.warning(f"任务超时 internal_id={internal_task_id} provider_task={provider_task_id} message={message_id}")
            self.task_failed.emit(message_id, error_msg)
            task_repo = self._session_manager.get_repo(ActiveTaskRepository)
            self._session_manager.begin_write()
            try:
                task_repo.mark_completed(internal_task_id)
                self._session_manager.commit_write()
            except Exception:
                self._session_manager.rollback_write()
                raise
            self._task_poll_count.pop(internal_task_id, None)
            return

        # 执行状态查询
        try:
            provider = self._service.get_provider(provider_name)
            result = provider.check_status(provider_task_id)
            self._task_poll_count[internal_task_id] = poll_count + 1

            self.status_changed.emit(message_id, result.status.value)
            task_repo = self._session_manager.get_repo(ActiveTaskRepository)
            self._session_manager.begin_write()
            try:
                task_repo.update_status(internal_task_id, result.status.value, video_url=result.video_url or "")
                self._session_manager.commit_write()
            except Exception:
                self._session_manager.rollback_write()
                raise

            if result.status == TaskStatus.SUCCEEDED:
                if not result.video_url:
                    raise RuntimeError("任务成功但未返回视频地址")
                self._download_and_finish(
                    provider=provider,
                    internal_task_id=internal_task_id,
                    message_id=message_id,
                    video_url=result.video_url,
                    model_name=model_name,
                    prompt=msg.content,
                    save_path=task_info.get("save_path", ""),
                    storyboard_id=task_info.get("storyboard_id", ""),
                )
            elif result.status == TaskStatus.FAILED:
                error_msg = result.error_message or "未知原因"
                task_repo = self._session_manager.get_repo(ActiveTaskRepository)
                self._session_manager.begin_write()
                try:
                    task_repo.update_status(internal_task_id, "failed", error_message=error_msg)
                    self._session_manager.commit_write()
                except Exception:
                    self._session_manager.rollback_write()
                    raise
                self.task_failed.emit(message_id, f"任务失败：{error_msg}")
                self._session_manager.begin_write()
                try:
                    task_repo.mark_completed(internal_task_id)
                    self._session_manager.commit_write()
                except Exception:
                    self._session_manager.rollback_write()
                    raise
                self._task_poll_count.pop(internal_task_id, None)

        except Exception as e:
            logger.warning(f"轮询异常 internal_id={internal_task_id} provider_task={provider_task_id}（第 {poll_count + 1} 次）：{e}")
            self._task_poll_count[internal_task_id] = poll_count + 1

    def _download_and_finish(
        self,
        provider: VideoProvider,
        internal_task_id: int,
        message_id: str,
        video_url: str,
        model_name: str,
        prompt: str,
        save_path: str = "",
        storyboard_id: int = 0,
    ) -> None:
        """下载视频并标记任务完成。"""
        try:
            # 确定保存路径：有 save_path 时为 workspace 相对路径，否则为对话视频
            workspace = paths.workspace_dir(self._root)
            if save_path:
                save_path = os.path.join(workspace, save_path)
            else:
                from datetime import datetime
                target_dir = paths.chat_dir(self._root)
                now = datetime.now()
                stamp = now.strftime("%Y%m%d_%H%M%S")
                safe_prompt = "".join(c for c in prompt[:20] if c.isalnum() or c in " _-").strip() or "video"
                filename = f"{stamp}_{model_name}_{safe_prompt}.mp4"
                save_path = os.path.join(target_dir, filename)

            os.makedirs(self._cache_dir, exist_ok=True)
            tmp_path = os.path.join(self._cache_dir, f"{uuid.uuid4().hex}.mp4.part")

            def on_progress(downloaded: int, total: int) -> None:
                self.download_progress.emit(message_id, downloaded, total)

            self.status_changed.emit(message_id, MessageStatus.DOWNLOADING.value)
            provider.download(video_url, tmp_path, progress_callback=on_progress)

            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            shutil.move(tmp_path, save_path)

            self.task_finished.emit(message_id, save_path, storyboard_id)

            task_repo = self._session_manager.get_repo(ActiveTaskRepository)
            self._session_manager.begin_write()
            try:
                task_repo.mark_completed(internal_task_id)
                self._session_manager.commit_write()
            except Exception:
                self._session_manager.rollback_write()
                raise

            self._task_poll_count.pop(internal_task_id, None)
            logger.info(f"任务完成 internal_id={internal_task_id} local_path={save_path}")

        except Exception as e:
            logger.exception(f"下载失败 internal_id={internal_task_id}")
            self.task_failed.emit(message_id, f"下载失败：{e}")

            task_repo = self._session_manager.get_repo(ActiveTaskRepository)
            self._session_manager.begin_write()
            try:
                task_repo.mark_completed(internal_task_id)
                self._session_manager.commit_write()
            except Exception:
                self._session_manager.rollback_write()
                raise

            self._task_poll_count.pop(internal_task_id, None)
