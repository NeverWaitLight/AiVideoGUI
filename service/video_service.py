"""视频生成业务编排：简化为任务提交和对话管理，轮询由 TaskPollingService 负责。"""

from __future__ import annotations

import json
from loguru import logger
import uuid
from datetime import datetime
from typing import Any

from PySide6.QtCore import QObject

from config.manager import ConfigManager
from models.conversation import Conversation
from models.enums import MessageStatus
from models.message import Message
from providers.video_base import VideoProvider
from providers.dashscope_video import DashScopeVideoProvider
from providers.seedance_video import SeedanceVideoProvider
from storage.session_manager import SessionManager
from storage.repositories.conversation_repository import ConversationRepository
from storage.repositories.message_repository import MessageRepository
from storage.repositories.active_task_repository import ActiveTaskRepository

_PROVIDER_REGISTRY: dict[str, type[VideoProvider]] = {
    "dashscope": DashScopeVideoProvider,
    "seedance": SeedanceVideoProvider,
}

class VideoService(QObject):
    """视频生成服务：编排 UI ↔ Provider，仅负责对话管理和任务提交。

    任务轮询由独立的 TaskPollingService 处理。
    """

    def __init__(
        self,
        session_manager: SessionManager,
        config: ConfigManager,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._sm = session_manager
        self._config = config
        self._providers: dict[str, VideoProvider] = {}

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

        # 注入 SessionManager（用于 OSS 缓存）
        if hasattr(provider, "set_session_manager"):
            provider.set_session_manager(self._sm)

        self._providers[name] = provider
        return provider

    # ---------- 对话 ----------

    def create_conversation(
        self, provider_name: str, model_name: str, title: str = "新对话", project_id: str = "", is_hidden: bool = False
    ) -> Conversation:
        conv = Conversation(
            id=uuid.uuid4().hex,
            title=title,
            created_at=datetime.now(),
            model_name=model_name,
            provider_name=provider_name,
            project_id=project_id,
            is_hidden=is_hidden,
        )

        conv_repo = self._sm.get_repo(ConversationRepository)
        self._sm.begin_write()
        try:
            conv_repo.save(conv)
            self._sm.commit_write()
            return conv
        except Exception as e:
            self._sm.rollback_write()
            logger.error(f"创建对话失败: {e}")
            raise

    def add_user_message(self, conversation_id: str, content: str) -> Message:
        msg = Message(
            id=uuid.uuid4().hex,
            conversation_id=conversation_id,
            role="user",
            content=content,
            created_at=datetime.now(),
            status=MessageStatus.COMPLETED,
        )

        msg_repo = self._sm.get_repo(MessageRepository)
        self._sm.begin_write()
        try:
            msg_repo.save(msg)
            self._sm.commit_write()
            return msg
        except Exception as e:
            self._sm.rollback_write()
            logger.error(f"添加用户消息失败: {e}")
            raise

    def add_assistant_message(self, conversation_id: str, content: str) -> Message:
        """添加助手消息（纯文本对话，不关联视频任务）。"""
        msg = Message(
            id=uuid.uuid4().hex,
            conversation_id=conversation_id,
            role="assistant",
            content=content,
            created_at=datetime.now(),
            status=MessageStatus.COMPLETED,
        )

        msg_repo = self._sm.get_repo(MessageRepository)
        self._sm.begin_write()
        try:
            msg_repo.save(msg)
            self._sm.commit_write()
            return msg
        except Exception as e:
            self._sm.rollback_write()
            logger.error(f"添加助手消息失败: {e}")
            raise

    # ---------- 提交任务 ----------

    def submit_task(
        self,
        conversation_id: str,
        prompt: str,
        provider_name: str,
        params: dict[str, Any] | None = None,
        save_path: str = "",
        storyboard_id: int = 0,
        reference_image: str = "",
    ) -> Message:
        """提交视频生成任务，写入数据库后由 TaskPollingService 接管轮询。

        Args:
            reference_image: 参考图路径（分镜设计图或角色设计图）。
                           如果提供，使用 r2v（参考生视频）；否则使用 t2v（文生视频）。
        """
        provider = self.get_provider(provider_name)

        # 智能路由：有参考图用 r2v，无参考图用 t2v
        if reference_image:
            provider_task_id, request_params = provider.r2v(prompt, reference_image, params)
            logger.info(f"使用参考生视频 (r2v)：reference_image={reference_image}")
        else:
            provider_task_id, request_params = provider.t2v(prompt, params)
            logger.info(f"使用文生视频 (t2v)")

        assistant_msg = Message(
            id=uuid.uuid4().hex,
            conversation_id=conversation_id,
            role="assistant",
            content="",
            created_at=datetime.now(),
            task_id=provider_task_id,
            status=MessageStatus.GENERATING,
        )

        msg_repo = self._sm.get_repo(MessageRepository)
        task_repo = self._sm.get_repo(ActiveTaskRepository)

        self._sm.begin_write()
        try:
            # 保存助手消息
            msg_repo.save(assistant_msg)

            # 添加活跃任务
            active_task_id = task_repo.add(
                provider_task_id=provider_task_id,
                message_id=assistant_msg.id,
                provider_name=provider_name,
                model_name=provider._config.default_model,
                save_path=save_path,
                request_params=json.dumps(request_params, ensure_ascii=False),
                storyboard_id=storyboard_id,
            )

            self._sm.commit_write()

            logger.info(
                "任务已提交 message=%s provider_task=%s active_task=%s provider=%s save_path=%s",
                assistant_msg.id,
                provider_task_id,
                active_task_id,
                provider_name,
                save_path,
            )
            return assistant_msg
        except Exception as e:
            self._sm.rollback_write()
            logger.error(f"提交任务失败: {e}")
            raise
