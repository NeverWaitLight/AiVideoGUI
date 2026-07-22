"""全局任务轮询服务：独立后台线程，按照 active_tasks 表驱动轮询策略。"""

from __future__ import annotations

import logging
import os
import shutil
import time
import uuid
from typing import Any

from PyQt6.QtCore import QObject, QThread, pyqtSignal

from config.manager import ConfigManager
from models.data_models import MessageStatus, TaskStatus
from providers.base import VideoProvider
from storage.database import DatabaseManager

logger = logging.getLogger(__name__)


class TaskPollingService(QObject):
    """全局任务轮询服务：应用启动时运行，根据 active_tasks 表自动启停。"""

    status_changed = pyqtSignal(str, str)
    download_progress = pyqtSignal(str, int, int)
    task_finished = pyqtSignal(str, str)
    task_failed = pyqtSignal(str, str)

    def __init__(
        self,
        db: DatabaseManager,
        config: ConfigManager,
        download_dir: str,
        temp_dir: str,
        provider_registry: dict[str, type[VideoProvider]],
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._db = db
        self._config = config
        self._download_dir = download_dir
        self._temp_dir = temp_dir
        self._provider_registry = provider_registry
        self._providers: dict[str, VideoProvider] = {}
        self._worker: _PollingWorker | None = None
        self._media_service: Any = None

        # 轮询策略配置
        self.poll_interval = 30.0  # 任务状态检查间隔（秒）
        self.initial_delay = 300.0  # 新任务提交后的初始等待时间（秒）
        self.idle_check_interval = 60.0  # 空闲时检查表是否有新任务的间隔（秒）
        self.max_polls_per_task = 50  # 单个任务最大轮询次数

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
        self._providers[name] = provider
        return provider

    def start(self) -> None:
        """启动全局轮询服务。"""
        if self._worker is not None:
            logger.warning("轮询服务已在运行")
            return
        self._worker = _PollingWorker(
            db=self._db,
            service=self,
            poll_interval=self.poll_interval,
            initial_delay=self.initial_delay,
            idle_check_interval=self.idle_check_interval,
            max_polls_per_task=self.max_polls_per_task,
            download_dir=self._download_dir,
            temp_dir=self._temp_dir,
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
        msg_status = MessageStatus(status)
        self._db.update_message_status(message_id, msg_status)
        self.status_changed.emit(message_id, status)

    def _on_download_progress(self, message_id: str, downloaded: int, total: int) -> None:
        self.download_progress.emit(message_id, downloaded, total)

    def _on_task_finished(self, message_id: str, local_path: str) -> None:
        msg = self._db.get_message(message_id)
        self._db.update_message_status(message_id, MessageStatus.COMPLETED, local_path=local_path)
        if msg and self._media_service:
            try:
                self._media_service.register_task_result(message_id, local_path, msg.conversation_id)
            except Exception as e:
                logger.warning("素材自动入库失败：%s", e)
        self.task_finished.emit(message_id, local_path)

    def _on_task_failed(self, message_id: str, error: str) -> None:
        self._db.update_message_status(message_id, MessageStatus.FAILED, error_message=error)
        self.task_failed.emit(message_id, error)


class _PollingWorker(QThread):
    """后台轮询线程：周期性扫描 active_tasks 表，按任务创建时间执行轮询策略。"""

    status_changed = pyqtSignal(str, str)
    download_progress = pyqtSignal(str, int, int)
    task_finished = pyqtSignal(str, str)
    task_failed = pyqtSignal(str, str)

    def __init__(
        self,
        db: DatabaseManager,
        service: TaskPollingService,
        poll_interval: float,
        initial_delay: float,
        idle_check_interval: float,
        max_polls_per_task: int,
        download_dir: str,
        temp_dir: str,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._db = db
        self._service = service
        self._poll_interval = poll_interval
        self._initial_delay = initial_delay
        self._idle_check_interval = idle_check_interval
        self._max_polls_per_task = max_polls_per_task
        self._download_dir = download_dir
        self._temp_dir = temp_dir
        self._stopped = False
        self._task_poll_count: dict[str, int] = {}  # task_id -> 已轮询次数

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
        while not self._stopped:
            try:
                tasks = self._db.list_active_tasks()
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
                logger.exception("轮询线程异常：%s", e)
                if self._interruptible_sleep(self._poll_interval):
                    break

        logger.info("轮询线程已退出")

    def _process_task(self, task_info: dict[str, Any]) -> None:
        """处理单个任务：检查是否需要轮询、执行状态查询、下载视频。"""
        task_id = task_info["task_id"]
        message_id = task_info["message_id"]
        provider_name = task_info["provider_name"]
        model_name = task_info["model_name"]
        created_at = task_info["created_at"]

        # 检查消息状态
        msg = self._db.get_message(message_id)
        if not msg:
            logger.warning("任务关联消息不存在，清理残留 task_id=%s", task_id)
            self._db.remove_active_task(task_id)
            self._task_poll_count.pop(task_id, None)
            return

        # 消息已是终态，清理任务
        if msg.status in (MessageStatus.COMPLETED, MessageStatus.FAILED):
            self._db.remove_active_task(task_id)
            self._task_poll_count.pop(task_id, None)
            return

        # 检查是否需要等待初始延迟
        elapsed_seconds = (time.time() - created_at.timestamp()) if created_at else 999999
        if elapsed_seconds < self._initial_delay:
            # 还在初始等待期，跳过此次轮询
            return

        # 检查是否超过最大轮询次数
        poll_count = self._task_poll_count.get(task_id, 0)
        if poll_count >= self._max_polls_per_task:
            error_msg = f"轮询超时（已查询 {poll_count} 次，任务仍未完成）"
            logger.warning("任务超时 task_id=%s message_id=%s", task_id, message_id)
            self.task_failed.emit(message_id, error_msg)
            self._db.remove_active_task(task_id)
            self._task_poll_count.pop(task_id, None)
            return

        # 执行状态查询
        try:
            provider = self._service.get_provider(provider_name)
            result = provider.check_status(task_id)
            self._task_poll_count[task_id] = poll_count + 1

            self.status_changed.emit(message_id, result.status.value)
            self._db.update_active_task(task_id, result.status.value, video_url=result.video_url or "")

            if result.status == TaskStatus.SUCCEEDED:
                if not result.video_url:
                    raise RuntimeError("任务成功但未返回视频地址")
                self._download_and_finish(
                    provider=provider,
                    task_id=task_id,
                    message_id=message_id,
                    video_url=result.video_url,
                    model_name=model_name,
                    prompt=msg.content,
                    save_path=task_info.get("save_path", ""),
                )
            elif result.status == TaskStatus.FAILED:
                error_msg = result.error_message or "未知原因"
                self.task_failed.emit(message_id, f"任务失败：{error_msg}")
                self._db.remove_active_task(task_id)
                self._task_poll_count.pop(task_id, None)

        except Exception as e:
            logger.warning("轮询异常 task_id=%s（第 %d 次）：%s", task_id, poll_count + 1, e)
            self._task_poll_count[task_id] = poll_count + 1

    def _download_and_finish(
        self,
        provider: VideoProvider,
        task_id: str,
        message_id: str,
        video_url: str,
        model_name: str,
        prompt: str,
        save_path: str = "",
    ) -> None:
        """下载视频并标记任务完成。"""
        try:
            # 如果任务提交时已预计算保存路径（相对路径），拼接到下载目录；否则按默认规则生成
            if save_path:
                save_path = os.path.join(self._download_dir, save_path)
            else:
                from datetime import datetime
                now = datetime.now()
                stamp = now.strftime("%Y%m%d_%H%M%S")
                safe_prompt = "".join(c for c in prompt[:20] if c.isalnum() or c in " _-").strip() or "video"
                filename = f"{stamp}_{model_name}_{safe_prompt}.mp4"
                save_path = os.path.join(self._download_dir, filename)

            os.makedirs(self._temp_dir, exist_ok=True)
            tmp_path = os.path.join(self._temp_dir, f"{uuid.uuid4().hex}.mp4.part")

            def on_progress(downloaded: int, total: int) -> None:
                self.download_progress.emit(message_id, downloaded, total)

            self.status_changed.emit(message_id, MessageStatus.DOWNLOADING.value)
            provider.download(video_url, tmp_path, progress_callback=on_progress)

            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            shutil.move(tmp_path, save_path)

            self.task_finished.emit(message_id, save_path)
            self._db.remove_active_task(task_id)
            self._task_poll_count.pop(task_id, None)
            logger.info("任务完成 task_id=%s local_path=%s", task_id, save_path)

        except Exception as e:
            logger.exception("下载失败 task_id=%s", task_id)
            self.task_failed.emit(message_id, f"下载失败：{e}")
            self._db.remove_active_task(task_id)
            self._task_poll_count.pop(task_id, None)
