"""视频生成业务编排：简化为任务提交和对话管理，轮询由 TaskPollingService 负责。"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime
from typing import Any

from PyQt6.QtCore import QObject

from config.manager import ConfigManager
from models.data_models import (
    Conversation,
    Message,
    MessageStatus,
)
from providers.base import VideoProvider
from providers.dashscope import DashScopeProvider
from storage.database import DatabaseManager

logger = logging.getLogger(__name__)

_PROVIDER_REGISTRY: dict[str, type[VideoProvider]] = {
    "dashscope": DashScopeProvider,
}


class VideoService(QObject):
    """视频生成服务：编排 UI ↔ Provider，仅负责对话管理和任务提交。

    任务轮询由独立的 TaskPollingService 处理。
    """

    def __init__(
        self,
        db: DatabaseManager,
        config: ConfigManager,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._db = db
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
        """提交视频生成任务，写入数据库后由 TaskPollingService 接管轮询。"""
        provider = self.get_provider(provider_name)
        task_id = provider.submit(prompt, params)

        assistant_msg = Message(
            id=uuid.uuid4().hex,
            conversation_id=conversation_id,
            role="assistant",
            content="",
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

        logger.info("任务已提交 message=%s task=%s provider=%s", assistant_msg.id, task_id, provider_name)
        return assistant_msg
