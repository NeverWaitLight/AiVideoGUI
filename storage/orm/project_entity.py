from typing import List, Optional

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class ProjectEntity(Base):
    __tablename__ = "projects"

    id: Mapped[Optional[int]] = mapped_column(Integer, primary_key=True, autoincrement=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    resolution: Mapped[str] = mapped_column(String(20), nullable=False, default="720P")
    aspect_ratio: Mapped[str] = mapped_column(String(10), nullable=False, default="16:9")
    cover_image: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    visual_style_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("visual_styles.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_at: Mapped[int] = mapped_column(Integer, nullable=False)

    story_outlines: Mapped[List["StoryOutlineEntity"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    screenplays: Mapped[List["ScreenplayEntity"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    characters: Mapped[List["CharacterEntity"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    visual_style: Mapped[Optional["VisualStyleEntity"]] = relationship()


class GenerateTaskEntity(Base):
    __tablename__ = "generate_tasks"

    id: Mapped[Optional[int]] = mapped_column(Integer, primary_key=True, autoincrement=True, nullable=False)

    type: Mapped[str] = mapped_column(String(20), nullable=False, default="video")
    provider_task_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    provider_name: Mapped[str] = mapped_column(String(50), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False, default="")

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    request_params: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    remote_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    local_path: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    error_message: Mapped[str] = mapped_column(Text, nullable=False, default="")

    caller_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    caller_id: Mapped[str] = mapped_column(String(100), nullable=False, default="")

    parent_ids: Mapped[str] = mapped_column(String(500), nullable=False, default="")

    created_at: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_at: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        Index("idx_generate_task_completed", "completed"),
        Index("idx_generate_task_provider_task_id", "provider_task_id"),
        Index("idx_generate_task_type", "type"),
        Index("idx_generate_task_caller", "caller_type", "caller_id"),
    )
