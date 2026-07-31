"""视频任务轮询任务：周期性扫描 active_tasks 表，轮询任务状态并下载视频。"""

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
from storage.repositories.active_task_repository import ActiveTaskRepository
from storage.repositories.message_repository import MessageRepository
from storage.repositories.oss_cache_repository import OSSFileCacheRepository
from utils import paths
from utils.path_converter import to_relative_path

if TYPE_CHECKING:
    from providers.video_base import VideoProvider


class VideoTaskPollingTask(BackgroundTask):
    """视频任务轮询任务（周期性任务）。

    工作流程：
    1. 周期性扫描 active_tasks 表
    2. 对每个活跃任务调用 Provider 查询状态
    3. 任务成功后下载视频并更新数据库
    4. 表空时进入低频检查模式

    注意：使用组合模式持有 QObject 信号发射器，避免多继承元类冲突。
    """

    def __init__(
        self,
        session_manager: SessionManager,
        provider_registry: dict[str, type[VideoProvider]],
        workspace_root: str,
        poll_interval: float = 10.0,
        idle_check_interval: float = 60.0,
        max_polls_per_task: int = 150,
    ) -> None:
        super().__init__(TaskType.PERIODIC, "video_task_polling")

        # 创建信号发射器（组合模式，避免多继承元类冲突）
        self._signal_emitter = _SignalEmitter()

        self._sm = session_manager
        self._provider_registry = provider_registry
        self._providers: dict[str, VideoProvider] = {}
        self._workspace_root = workspace_root
        self._cache_dir = paths.cache_dir(workspace_root)

        # 轮询策略配置
        self._poll_interval = poll_interval
        self._idle_check_interval = idle_check_interval
        self._max_polls_per_task = max_polls_per_task

        # 任务轮询计数
        self._task_poll_count: dict[int, int] = {}

        # 上次清理时间
        self._last_cleanup_time = time.time()
        self._cleanup_interval = 3600.0  # 每小时清理一次

        # 上次检查时间（用于动态间隔）
        self._last_check_time = time.time()

        # 外部依赖（可选）
        self._media_service: Any = None
        self._config_manager: Any = None

        # 启用任务（周期性任务默认启用）
        self.enable()

    @property
    def signal_emitter(self) -> QObject:
        """返回信号发射器（供外部连接信号）。"""
        return self._signal_emitter

    def set_media_service(self, media_service: Any) -> None:
        """注入素材库服务，用于任务完成后自动入库。"""
        self._media_service = media_service

    def set_config_manager(self, config_manager: Any) -> None:
        """注入配置管理器，用于获取 Provider 配置。"""
        self._config_manager = config_manager

    def get_provider(self, name: str) -> VideoProvider:
        """获取或创建 Provider 实例（延迟加载 + 缓存）。"""
        if name in self._providers:
            return self._providers[name]

        if self._config_manager is None:
            raise RuntimeError("ConfigManager 未注入")

        cfg = self._config_manager.get_provider(name)
        if cfg is None:
            raise KeyError(f"未配置的 Provider：{name}")

        cls = self._provider_registry.get(name)
        if cls is None:
            raise KeyError(f"未注册的 Provider：{name}")

        provider = cls(cfg)

        # 注入 SessionManager（用于 OSS 缓存）
        if hasattr(provider, "set_session_manager"):
            provider.set_session_manager(self._sm)

        self._providers[name] = provider
        return provider

    def execute(self) -> None:
        """执行一次轮询检查。"""
        try:
            # 定期清理过期 OSS 缓存
            now = time.time()
            if now - self._last_cleanup_time >= self._cleanup_interval:
                self._cleanup_expired_oss_caches()
                self._last_cleanup_time = now

            task_repo = self._sm.get_repo(ActiveTaskRepository)
            tasks = task_repo.list_active_tasks()

            if not tasks:
                # 表空，延长下次检查间隔
                time.sleep(self._idle_check_interval)
                return

            # 处理每个活跃任务
            for task_info in tasks:
                self._process_task(task_info)

            # 正常轮询间隔
            self._last_check_time = now

        except Exception as e:
            logger.exception(f"轮询任务执行异常：{e}")

    def _cleanup_expired_oss_caches(self) -> None:
        """清理过期的 OSS 缓存记录。"""
        try:
            oss_cache_repo = self._sm.get_repo(OSSFileCacheRepository)
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
        """处理单个任务：检查是否需要轮询、执行状态查询、下载视频。"""
        internal_task_id = task_info["id"]
        provider_task_id = task_info["provider_task_id"]
        message_id = task_info["message_id"]
        provider_name = task_info["provider_name"]
        model_name = task_info["model_name"]

        # 检查消息状态
        msg_repo = self._sm.get_repo(MessageRepository)
        msg = msg_repo.get_by_id(message_id)
        if not msg:
            logger.warning(f"任务关联消息不存在，标记完成 internal_id={internal_task_id}")
            self._mark_task_completed(internal_task_id)
            return

        # 消息已是终态，标记任务完成
        if msg.status in (MessageStatus.COMPLETED, MessageStatus.FAILED):
            self._mark_task_completed(internal_task_id)
            return

        # 检查是否超过最大轮询次数
        poll_count = self._task_poll_count.get(internal_task_id, 0)
        if poll_count >= self._max_polls_per_task:
            error_msg = f"轮询超时（已查询 {poll_count} 次，任务仍未完成）"
            logger.warning(f"任务超时 internal_id={internal_task_id}")
            self._handle_task_failed(message_id, internal_task_id, error_msg)
            return

        # 执行状态查询
        try:
            provider = self.get_provider(provider_name)
            result = provider.check_status(provider_task_id)
            self._task_poll_count[internal_task_id] = poll_count + 1

            # 更新任务状态
            task_repo = self._sm.get_repo(ActiveTaskRepository)
            self._sm.begin_write()
            try:
                task_repo.update_status(internal_task_id, result.status.value, video_url=result.video_url or "")
                self._sm.commit_write()
            except Exception:
                self._sm.rollback_write()
                raise

            # 更新消息状态
            self._update_message_status(message_id, result.status.value)

            # 发送状态变化信号
            self._signal_emitter.status_changed.emit(message_id, result.status.value)

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
                    storyboard_id=task_info.get("storyboard_id", 0),
                )
            elif result.status == TaskStatus.FAILED:
                error_msg = result.error_message or "未知原因"
                self._handle_task_failed(message_id, internal_task_id, f"任务失败：{error_msg}")
                # 发送失败信号
                self._signal_emitter.task_failed.emit(message_id, f"任务失败：{error_msg}")

        except Exception as e:
            logger.warning(f"轮询异常 internal_id={internal_task_id}（第 {poll_count + 1} 次）：{e}")
            self._task_poll_count[internal_task_id] = poll_count + 1

    def _mark_task_completed(self, internal_task_id: int) -> None:
        """标记任务完成并清理计数。"""
        task_repo = self._sm.get_repo(ActiveTaskRepository)
        self._sm.begin_write()
        try:
            task_repo.mark_completed(internal_task_id)
            self._sm.commit_write()
        except Exception:
            self._sm.rollback_write()
            raise
        self._task_poll_count.pop(internal_task_id, None)

    def _update_message_status(self, message_id: str, task_status: str) -> None:
        """根据任务状态更新消息状态。"""
        _TASK_TO_MSG_STATUS = {
            "pending": MessageStatus.GENERATING,
            "running": MessageStatus.GENERATING,
            "succeeded": MessageStatus.COMPLETED,
            "failed": MessageStatus.FAILED,
        }
        msg_status = _TASK_TO_MSG_STATUS.get(task_status)
        if msg_status is not None:
            msg_repo = self._sm.get_repo(MessageRepository)
            self._sm.begin_write()
            try:
                msg_repo.update_status(message_id, msg_status)
                self._sm.commit_write()
            except Exception:
                self._sm.rollback_write()
                raise

    def _handle_task_failed(self, message_id: str, internal_task_id: int, error: str) -> None:
        """处理任务失败。"""
        msg_repo = self._sm.get_repo(MessageRepository)
        self._sm.begin_write()
        try:
            msg_repo.update_status(message_id, MessageStatus.FAILED, error_message=error)
            self._sm.commit_write()
        except Exception:
            self._sm.rollback_write()
            raise
        self._mark_task_completed(internal_task_id)
        # 发送失败信号
        self._signal_emitter.task_failed.emit(message_id, error)

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
            # 确定保存路径
            workspace = paths.workspace_dir(self._workspace_root)
            if save_path:
                save_path = os.path.join(workspace, save_path)
            else:
                from datetime import datetime
                target_dir = paths.chat_dir(self._workspace_root)
                now = datetime.now()
                stamp = now.strftime("%Y%m%d_%H%M%S")
                safe_prompt = "".join(c for c in prompt[:20] if c.isalnum() or c in " _-").strip() or "video"
                filename = f"{stamp}_{model_name}_{safe_prompt}.mp4"
                save_path = os.path.join(target_dir, filename)

            os.makedirs(self._cache_dir, exist_ok=True)
            tmp_path = os.path.join(self._cache_dir, f"{uuid.uuid4().hex}.mp4.part")

            # 下载视频
            self._update_message_status(message_id, MessageStatus.DOWNLOADING.value)
            provider.download(video_url, tmp_path, progress_callback=None)

            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            shutil.move(tmp_path, save_path)

            # 转换为相对路径存储
            relative_save_path = to_relative_path(save_path, self._workspace_root)

            # 更新消息
            msg_repo = self._sm.get_repo(MessageRepository)
            self._sm.begin_write()
            try:
                msg_repo.update_status(message_id, MessageStatus.COMPLETED, local_path=relative_save_path)
                self._sm.commit_write()
            except Exception:
                self._sm.rollback_write()
                raise

            # 自动入库
            if self._media_service:
                msg = msg_repo.get_by_id(message_id)
                if msg:
                    try:
                        self._media_service.register_task_result(
                            message_id, save_path, msg.conversation_id, storyboard_id=storyboard_id
                        )
                    except Exception as e:
                        logger.warning(f"素材自动入库失败：{e}")

            self._mark_task_completed(internal_task_id)
            logger.info(f"任务完成 internal_id={internal_task_id} local_path={save_path}")

            # 发送完成信号
            self._signal_emitter.task_finished.emit(message_id, save_path, storyboard_id)

        except Exception as e:
            logger.exception(f"下载失败 internal_id={internal_task_id}")
            self._handle_task_failed(message_id, internal_task_id, f"下载失败：{e}")

    def should_continue(self) -> bool:
        """周期性任务始终返回 True。"""
        return True

    def get_interval(self) -> float:
        """返回轮询间隔（秒）。"""
        return self._poll_interval


class _SignalEmitter(QObject):
    """信号发射器（独立的 QObject，避免多继承元类冲突）。"""

    status_changed = Signal(str, str)  # message_id, status
    download_progress = Signal(str, int, int)  # message_id, downloaded, total
    task_finished = Signal(str, str, int)  # message_id, local_path, storyboard_id
    task_failed = Signal(str, str)  # message_id, error

