from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class ProjectEntity(Base):
    __tablename__ = "projects"

    id: Mapped[Optional[int]] = mapped_column(Integer, primary_key=True, autoincrement=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    resolution: Mapped[str] = mapped_column(String(20), nullable=False, default="720P")
    aspect_ratio: Mapped[str] = mapped_column(String(10), nullable=False, default="16:9")
    cover_image: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    created_at: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_at: Mapped[int] = mapped_column(Integer, nullable=False)

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

    project: Mapped[Optional["ProjectEntity"]] = relationship(back_populates="conversations")
    messages: Mapped[List["MessageEntity"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_conversations_project", "project_id"),
        Index("idx_conversations_created", "created_at"),
    )


class MessageEntity(Base):
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

    conversation: Mapped["ConversationEntity"] = relationship(back_populates="messages")
    active_task: Mapped[Optional["ActiveTaskEntity"]] = relationship(
        back_populates="message", cascade="all, delete-orphan", uselist=False
    )

    __table_args__ = (Index("idx_messages_conversation", "conversation_id", "created_at"),)


class ActiveTaskEntity(Base):
    __tablename__ = "active_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    provider_task_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    message_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False
    )

    provider_name: Mapped[str] = mapped_column(String(50), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False, default="")

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    request_params: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    video_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    save_path: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    error_message: Mapped[str] = mapped_column(Text, nullable=False, default="")

    storyboard_id: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    message: Mapped["MessageEntity"] = relationship(back_populates="active_task")

    __table_args__ = (
        Index("idx_active_task_completed", "completed"),
        Index("idx_active_task_provider_task_id", "provider_task_id"),
    )
