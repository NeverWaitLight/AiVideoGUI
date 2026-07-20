"""视频生成业务编排：submit → poll → download。"""

from __future__ import annotations

import logging
import os
import shutil
import time
import uuid
from datetime import datetime
from typing import Any

from PyQt6.QtCore import QObject, QThread, pyqtSignal

from config.manager import ConfigManager
from models.data_models import (
    Conversation,
    Message,
    MessageStatus,
    ProviderConfig,
    TaskStatus,
)
from providers.base import VideoProvider
from providers.dashscope import DashScopeProvider
from storage.database import DatabaseManager

logger = logging.getLogger(__name__)

_PROVIDER_REGISTRY: dict[str, type[VideoProvider]] = {
    "dashscope": DashScopeProvider,
}


def _build_video_filename(model_name: str, prompt: str) -> str:
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    safe_prompt = "".join(c for c in prompt[:20] if c.isalnum() or c in " _-").strip() or "video"
    return f"{stamp}_{model_name}_{safe_prompt}.mp4"


class _TaskWorker(QThread):
    """后台线程：轮询任务直到终态，再下载视频。"""

    status_changed = pyqtSignal(str, str)
    download_progress = pyqtSignal(str, int, int)
    finished = pyqtSignal(str, str)
    failed = pyqtSignal(str, str)

    def __init__(
        self,
        provider: VideoProvider,
        task_id: str,
        message_id: str,
        save_path: str,
        temp_dir: str,
        poll_interval: float = 30.0,
        poll_delay: float = 300.0,
        max_polls: int = 50,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._provider = provider
        self._task_id = task_id
        self._message_id = message_id
        self._save_path = save_path
        self._temp_dir = temp_dir
        self._poll_interval = poll_interval
        self._poll_delay = poll_delay
        self._max_polls = max_polls
        self._stopped = False

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
        try:
            if self._poll_delay > 0:
                logger.info("等待 %.0f 秒后开始轮询 task_id=%s", self._poll_delay, self._task_id)
                if self._interruptible_sleep(self._poll_delay):
                    return
            video_url = self._poll_until_done()
            if self._stopped:
                return
            local_path = self._download(video_url)
            self.finished.emit(self._message_id, local_path)
        except Exception as e:
            logger.exception("任务执行失败 task_id=%s", self._task_id)
            self.failed.emit(self._message_id, str(e))

    def _poll_until_done(self) -> str:
        for i in range(self._max_polls):
            if self._stopped:
                return ""
            try:
                result = self._provider.check_status(self._task_id)
            except Exception as e:
                logger.warning("轮询异常（第 %d 次）：%s", i + 1, e)
                self._interruptible_sleep(self._poll_interval)
                continue

            self.status_changed.emit(self._message_id, result.status.value)

            if result.status == TaskStatus.SUCCEEDED:
                if not result.video_url:
                    raise RuntimeError("任务成功但未返回视频地址")
                return result.video_url
            if result.status == TaskStatus.FAILED:
                raise RuntimeError(f"任务失败：{result.error_message or '未知原因'}")

            if i < self._max_polls - 1:
                self._interruptible_sleep(self._poll_interval)

        total_minutes = (self._poll_delay + self._max_polls * self._poll_interval) / 60
        raise TimeoutError(
            f"轮询超时（已等待 {total_minutes:.0f} 分钟，共查询 {self._max_polls} 次，任务仍未完成）"
        )

    def _download(self, video_url: str) -> str:
        os.makedirs(self._temp_dir, exist_ok=True)
        tmp_path = os.path.join(self._temp_dir, f"{uuid.uuid4().hex}.mp4.part")

        def on_progress(downloaded: int, total: int) -> None:
            self.download_progress.emit(self._message_id, downloaded, total)

        self.status_changed.emit(self._message_id, MessageStatus.DOWNLOADING.value)
        self._provider.download(video_url, tmp_path, progress_callback=on_progress)

        os.makedirs(os.path.dirname(self._save_path), exist_ok=True)
        shutil.move(tmp_path, self._save_path)
        return self._save_path


class VideoService(QObject):
    """视频生成服务：编排 UI ↔ Provider，管理任务生命周期。"""

    status_changed = pyqtSignal(str, str)
    download_progress = pyqtSignal(str, int, int)
    task_finished = pyqtSignal(str, str)
    task_failed = pyqtSignal(str, str)

    def __init__(
        self,
        db: DatabaseManager,
        config: ConfigManager,
        download_dir: str = "",
        temp_dir: str = "",
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._db = db
        self._config = config
        self._download_dir = download_dir or self._default_download_dir()
        self._temp_dir = temp_dir or self._default_temp_dir()
        self._workers: dict[str, _TaskWorker] = {}
        self._message_tasks: dict[str, str] = {}
        self._message_conv: dict[str, str] = {}
        self._providers: dict[str, VideoProvider] = {}
        self._media_service: Any = None
        self.poll_delay: float = 300.0
        self.poll_interval: float = 30.0
        self.max_polls: int = 50

    def set_media_service(self, media_service: Any) -> None:
        """注入素材库服务，用于任务完成后自动入库。"""
        self._media_service = media_service

    @staticmethod
    def _default_download_dir() -> str:
        home = os.path.expanduser("~")
        return os.path.join(home, "Videos", "AI-Video-GUI")

    @staticmethod
    def _default_temp_dir() -> str:
        return os.path.join(os.environ.get("TEMP", os.path.expanduser("~")), "ai-video-gui")

    # ---------- provider ----------

    def get_provider(self, name: str) -> VideoProvider:
        if name in self._providers:
            return self._providers[name]
        cfg = self._config.get_provider(name)
        if cfg is None:
            raise KeyError(f"未配置的 Provider：{name}")
        cls = _PROVIDER_REGISTRY.get(name)
        if cls is None:
            raise KeyError(f"未注册的 Provider：{name}")
        provider = cls(cfg)
        self._providers[name] = provider
        return provider

    # ---------- 对话 ----------

    def create_conversation(self, provider_name: str, model_name: str, title: str = "新对话") -> Conversation:
        conv = Conversation(
            id=uuid.uuid4().hex,
            title=title,
            created_at=datetime.now(),
            model_name=model_name,
            provider_name=provider_name,
        )
        self._db.create_conversation(conv)
        return conv

    def add_user_message(self, conversation_id: str, content: str) -> Message:
        msg = Message(
            id=uuid.uuid4().hex,
            conversation_id=conversation_id,
            role="user",
            content=content,
            created_at=datetime.now(),
            status=MessageStatus.COMPLETED,
        )
        self._db.add_message(msg)
        return msg

    # ---------- 提交任务 ----------

    def submit_task(
        self,
        conversation_id: str,
        prompt: str,
        provider_name: str,
        params: dict[str, Any] | None = None,
    ) -> Message:
        provider = self.get_provider(provider_name)
        task_id = provider.submit(prompt, params)

        assistant_msg = Message(
            id=uuid.uuid4().hex,
            conversation_id=conversation_id,
            role="assistant",
            content=prompt,
            created_at=datetime.now(),
            task_id=task_id,
            status=MessageStatus.GENERATING,
        )
        self._db.add_message(assistant_msg)
        self._db.add_active_task(
            task_id=task_id,
            message_id=assistant_msg.id,
            provider_name=provider_name,
            model_name=provider._config.default_model,
        )

        filename = _build_video_filename(provider._config.default_model, prompt)
        save_path = os.path.join(self._download_dir, filename)

        worker = _TaskWorker(
            provider=provider,
            task_id=task_id,
            message_id=assistant_msg.id,
            save_path=save_path,
            temp_dir=self._temp_dir,
            poll_interval=self.poll_interval,
            poll_delay=self.poll_delay,
            max_polls=self.max_polls,
        )
        worker.status_changed.connect(self._on_status_changed)
        worker.download_progress.connect(self._on_download_progress)
        worker.finished.connect(self._on_finished)
        worker.failed.connect(self._on_failed)
        self._workers[assistant_msg.id] = worker
        self._message_tasks[assistant_msg.id] = task_id
        self._message_conv[assistant_msg.id] = conversation_id
        worker.start()

        logger.info("任务已启动 message=%s task=%s", assistant_msg.id, task_id)
        return assistant_msg

    # ---------- worker 信号处理 ----------

    def _on_status_changed(self, message_id: str, status: str) -> None:
        try:
            msg_status = MessageStatus(status)
        except ValueError:
            msg_status = MessageStatus.GENERATING
        self._db.update_message_status(message_id, msg_status)
        self.status_changed.emit(message_id, status)

    def _on_download_progress(self, message_id: str, downloaded: int, total: int) -> None:
        self.download_progress.emit(message_id, downloaded, total)

    def _on_finished(self, message_id: str, local_path: str) -> None:
        self._db.update_message_status(message_id, MessageStatus.COMPLETED, local_path=local_path)
        conv_id = self._message_conv.get(message_id, "")
        if self._media_service:
            try:
                self._media_service.register_task_result(message_id, local_path, conv_id)
            except Exception as e:
                logger.warning("素材自动入库失败：%s", e)
        self._cleanup_worker(message_id)
        self.task_finished.emit(message_id, local_path)

    def _on_failed(self, message_id: str, error: str) -> None:
        self._db.update_message_status(
            message_id, MessageStatus.FAILED, error_message=error
        )
        self._cleanup_worker(message_id)
        self.task_failed.emit(message_id, error)

    def _cleanup_worker(self, message_id: str) -> None:
        worker = self._workers.pop(message_id, None)
        if worker:
            worker.deleteLater()
        task_id = self._message_tasks.pop(message_id, None)
        if task_id:
            self._db.remove_active_task(task_id)
        self._message_conv.pop(message_id, None)

    # ---------- 恢复未完成任务 ----------

    def resume_pending_tasks(self) -> int:
        """启动时恢复 active_tasks 表中仍在等待的任务轮询。

        返回成功恢复的任务数量。
        """
        active = self._db.list_active_tasks()
        resumed = 0
        for task in active:
            task_id = task["task_id"]
            message_id = task["message_id"]
            provider_name = task["provider_name"]
            model_name = task["model_name"]

            # 跳过已有 worker 的任务（理论上不应出现）
            if message_id in self._workers:
                continue

            # 获取消息以拿到 conversation_id 和 prompt
            msg = self._db.get_message(message_id)
            if not msg:
                logger.warning("恢复任务失败：消息不存在 message_id=%s", message_id)
                self._db.remove_active_task(task_id)
                continue

            # 消息已经是终态，清理残留记录
            if msg.status in (MessageStatus.COMPLETED, MessageStatus.FAILED):
                self._db.remove_active_task(task_id)
                continue

            try:
                provider = self.get_provider(provider_name)
            except Exception as e:
                logger.warning("恢复任务失败：Provider 不可用 %s — %s", provider_name, e)
                self._db.update_message_status(
                    message_id, MessageStatus.FAILED,
                    error_message=f"Provider {provider_name} 不可用，任务已中断",
                )
                self._db.remove_active_task(task_id)
                continue

            filename = _build_video_filename(model_name, msg.content)
            save_path = os.path.join(self._download_dir, filename)

            worker = _TaskWorker(
                provider=provider,
                task_id=task_id,
                message_id=message_id,
                save_path=save_path,
                temp_dir=self._temp_dir,
                poll_interval=self.poll_interval,
                poll_delay=0.0,
                max_polls=self.max_polls,
            )
            worker.status_changed.connect(self._on_status_changed)
            worker.download_progress.connect(self._on_download_progress)
            worker.finished.connect(self._on_finished)
            worker.failed.connect(self._on_failed)
            self._workers[message_id] = worker
            self._message_tasks[message_id] = task_id
            self._message_conv[message_id] = msg.conversation_id
            worker.start()
            resumed += 1
            logger.info("已恢复任务轮询 message=%s task=%s", message_id, task_id)

        if resumed:
            logger.info("共恢复 %d 个未完成任务", resumed)
        return resumed

    # ---------- 生命周期 ----------

    def shutdown(self) -> None:
        for w in list(self._workers.values()):
            w.stop()
            w.wait(2000)
        self._workers.clear()
