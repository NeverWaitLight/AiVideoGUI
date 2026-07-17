"""视频生成业务编排：submit → poll → download。"""

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
        poll_interval: float = 5.0,
        max_polls: int = 240,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._provider = provider
        self._task_id = task_id
        self._message_id = message_id
        self._save_path = save_path
        self._temp_dir = temp_dir
        self._poll_interval = poll_interval
        self._max_polls = max_polls
        self._stopped = False

    def stop(self) -> None:
        self._stopped = True

    def run(self) -> None:
        try:
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
                time.sleep(self._poll_interval)
                continue

            self.status_changed.emit(self._message_id, result.status.value)

            if result.status == TaskStatus.SUCCEEDED:
                if not result.video_url:
                    raise RuntimeError("任务成功但未返回视频地址")
                return result.video_url
            if result.status == TaskStatus.FAILED:
                raise RuntimeError(f"任务失败：{result.error_message or '未知原因'}")

            time.sleep(self._poll_interval)

        raise TimeoutError(f"轮询超时（{self._max_polls} 次）")

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
        self._providers: dict[str, VideoProvider] = {}

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
        )
        worker.status_changed.connect(self._on_status_changed)
        worker.download_progress.connect(self._on_download_progress)
        worker.finished.connect(self._on_finished)
        worker.failed.connect(self._on_failed)
        self._workers[assistant_msg.id] = worker
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
        self._cleanup_worker(message_id)
        self.task_finished.emit(message_id, local_path)

    def _on_failed(self, message_id: str, error: str) -> None:
        self._db.update_message_status(message_id, MessageStatus.FAILED)
        self._cleanup_worker(message_id)
        self.task_failed.emit(message_id, error)

    def _cleanup_worker(self, message_id: str) -> None:
        worker = self._workers.pop(message_id, None)
        if worker:
            worker.deleteLater()

    # ---------- 生命周期 ----------

    def shutdown(self) -> None:
        for w in list(self._workers.values()):
            w.stop()
            w.wait(2000)
        self._workers.clear()
