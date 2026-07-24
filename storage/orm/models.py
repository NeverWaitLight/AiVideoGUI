"""SQLAlchemy ORM 实体模型定义。"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class ProjectEntity(Base):
    """项目表。"""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    resolution: Mapped[str] = mapped_column(String(20), nullable=False, default="720P")
    aspect_ratio: Mapped[str] = mapped_column(String(10), nullable=False, default="16:9")
    cover_image: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False)  # 13位时间戳（毫秒）
    updated_at: Mapped[int] = mapped_column(BigInteger, nullable=False)  # 13位时间戳（毫秒）

    # 关系（一对多）
    conversations: Mapped[List["ConversationEntity"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    outlines: Mapped[List["OutlineEntity"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    scripts: Mapped[List["ScriptEntity"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    shot_histories: Mapped[List["ShotHistoryEntity"]] = relationship(
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
        BigInteger, ForeignKey("projects.id", ondelete="SET NULL"), nullable=False, default=0
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

    # 视频生成参数
    prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    video_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    save_path: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    error_message: Mapped[str] = mapped_column(Text, nullable=False, default="")

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


class MediaFileEntity(Base):
    """素材文件表。"""

    __tablename__ = "media_files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    media_type: Mapped[str] = mapped_column(String(20), nullable=False)
    local_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="task")
    conversation_id: Mapped[str] = mapped_column(String(36), nullable=False, default="")
    message_id: Mapped[str] = mapped_column(String(36), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # 视频元数据
    thumbnail_path: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    duration: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    width: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    height: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # 索引
    __table_args__ = (
        Index("idx_media_type", "media_type"),
        Index("idx_media_created", "created_at"),
    )


class OutlineEntity(Base):
    """大纲表。"""

    __tablename__ = "outlines"

    id: Mapped[Optional[int]] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False)  # 13位时间戳（毫秒）
    updated_at: Mapped[int] = mapped_column(BigInteger, nullable=False)  # 13位时间戳（毫秒）

    # 关系
    project: Mapped["ProjectEntity"] = relationship(back_populates="outlines")
    history: Mapped[List["OutlineHistoryEntity"]] = relationship(
        back_populates="outline", cascade="all, delete-orphan"
    )

    # 索引
    __table_args__ = (Index("idx_outline_project", "project_id"),)


class OutlineHistoryEntity(Base):
    """大纲历史表。"""

    __tablename__ = "outline_history"

    id: Mapped[Optional[int]] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    raw_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("outlines.id", ondelete="CASCADE"), nullable=False
    )
    project_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False)  # 13位时间戳（毫秒）

    # 关系
    outline: Mapped["OutlineEntity"] = relationship(back_populates="history")

    # 索引
    __table_args__ = (Index("idx_history_outline", "raw_id", "created_at"),)


class ScriptEntity(Base):
    """剧本表。"""

    __tablename__ = "scripts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # 关系
    project: Mapped["ProjectEntity"] = relationship(back_populates="scripts")
    scenes: Mapped[List["SceneEntity"]] = relationship(
        back_populates="script", cascade="all, delete-orphan"
    )
    history: Mapped[List["ScriptHistoryEntity"]] = relationship(
        back_populates="script", cascade="all, delete-orphan"
    )

    # 索引
    __table_args__ = (Index("idx_script_project", "project_id"),)


class SceneEntity(Base):
    """场次表。"""

    __tablename__ = "scenes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    script_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False
    )
    scene_number: Mapped[int] = mapped_column(Integer, nullable=False)
    location_type: Mapped[str] = mapped_column(String(50), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    time_type: Mapped[str] = mapped_column(String(50), nullable=False)
    time_detail: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # 关系
    script: Mapped["ScriptEntity"] = relationship(back_populates="scenes")
    shots: Mapped[List["ShotEntity"]] = relationship(
        back_populates="scene", cascade="all, delete-orphan"
    )

    # 索引
    __table_args__ = (Index("idx_scene_script", "script_id", "scene_number"),)


class ScriptHistoryEntity(Base):
    """剧本历史表。"""

    __tablename__ = "script_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    script_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    scenes_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # 关系
    script: Mapped["ScriptEntity"] = relationship(back_populates="history")

    # 索引
    __table_args__ = (Index("idx_history_script", "script_id", "created_at"),)


class ShotEntity(Base):
    """分镜表。"""

    __tablename__ = "shots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    scene_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("scenes.id", ondelete="CASCADE"), nullable=False
    )
    scene_number: Mapped[int] = mapped_column(Integer, nullable=False)
    shot_number: Mapped[int] = mapped_column(Integer, nullable=False)
    design_image: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    shot_size: Mapped[str] = mapped_column(String(50), nullable=False, default="medium_shot")
    camera_movement: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    visual_content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    dialogue: Mapped[str] = mapped_column(Text, nullable=False, default="")
    sound_effect: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    duration: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # 关系
    scene: Mapped["SceneEntity"] = relationship(back_populates="shots")

    # 索引
    __table_args__ = (
        Index("idx_shot_scene", "scene_id", "shot_number"),
        Index("idx_shot_scene_number", "scene_number"),
    )


class ShotHistoryEntity(Base):
    """分镜历史表。"""

    __tablename__ = "shot_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    shots_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # 关系
    project: Mapped["ProjectEntity"] = relationship(back_populates="shot_histories")

    # 索引
    __table_args__ = (Index("idx_history_shot", "project_id", "created_at"),)


class CharacterEntity(Base):
    """角色表。"""

    __tablename__ = "characters"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    project_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    ref_code: Mapped[str] = mapped_column(String(100), nullable=False)
    design_image: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # 关系
    project: Mapped["ProjectEntity"] = relationship(back_populates="characters")
    history: Mapped[List["CharacterHistoryEntity"]] = relationship(
        back_populates="character", cascade="all, delete-orphan"
    )

    # 索引
    __table_args__ = (
        Index("idx_character_project", "project_id"),
        Index("idx_character_ref_code", "project_id", "ref_code"),
    )


class CharacterHistoryEntity(Base):
    """角色编辑历史表。"""

    __tablename__ = "character_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    character_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("characters.uuid", ondelete="CASCADE"), nullable=False
    )
    snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # 关系
    character: Mapped["CharacterEntity"] = relationship(back_populates="history")

    # 索引
    __table_args__ = (Index("idx_history_character", "character_id", "created_at"),)
