"""项目相关实体模型定义。"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class ProjectEntity(Base):
    """项目表。"""

    __tablename__ = "projects"

    id: Mapped[Optional[int]] = mapped_column(Integer, primary_key=True, autoincrement=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    resolution: Mapped[str] = mapped_column(String(20), nullable=False, default="720P")
    aspect_ratio: Mapped[str] = mapped_column(String(10), nullable=False, default="16:9")
    cover_image: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    created_at: Mapped[int] = mapped_column(Integer, nullable=False)  # 13位时间戳（毫秒）
    updated_at: Mapped[int] = mapped_column(Integer, nullable=False)  # 13位时间戳（毫秒）

    # 关系（一对多）
    conversations: Mapped[List["ConversationEntity"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    story_outlines: Mapped[List["StoryOutlineEntity"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    screenplays: Mapped[List["ScreenplayEntity"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    characters: Mapped[List["CharacterEntity"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


class ConversationEntity(Base):
    """对话表。"""

    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    provider_name: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=False, default=0
    )
    is_hidden: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # 关系
    project: Mapped[Optional["ProjectEntity"]] = relationship(back_populates="conversations")
    messages: Mapped[List["MessageEntity"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )

    # 索引
    __table_args__ = (
        Index("idx_conversations_project", "project_id"),
        Index("idx_conversations_created", "created_at"),
    )


class MessageEntity(Base):
    """消息表。"""

    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    task_id: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    video_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    local_path: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="generating")
    error_message: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # 关系
    conversation: Mapped["ConversationEntity"] = relationship(back_populates="messages")
    active_task: Mapped[Optional["ActiveTaskEntity"]] = relationship(
        back_populates="message", cascade="all, delete-orphan", uselist=False
    )

    # 索引
    __table_args__ = (Index("idx_messages_conversation", "conversation_id", "created_at"),)


class ActiveTaskEntity(Base):
    """活跃任务表。"""

    __tablename__ = "active_tasks"

    # 自增主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Provider 任务 ID（原 task_id）
    provider_task_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    # 外键关联
    message_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False
    )

    # Provider 元数据
    provider_name: Mapped[str] = mapped_column(String(50), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False, default="")

    # 任务状态
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # 视频生成请求参数（完整 JSON）
    request_params: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    video_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    save_path: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    error_message: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # 分镜关联（可选，用于追踪视频生成来源）
    storyboard_id: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 关系
    message: Mapped["MessageEntity"] = relationship(back_populates="active_task")

    # 索引
    __table_args__ = (
        Index("idx_active_task_completed", "completed"),
        Index("idx_active_task_provider_task_id", "provider_task_id"),
    )
