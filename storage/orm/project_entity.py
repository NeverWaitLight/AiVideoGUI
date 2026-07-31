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

    story_outlines: Mapped[List["StoryOutlineEntity"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    screenplays: Mapped[List["ScreenplayEntity"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    characters: Mapped[List["CharacterEntity"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


class ActiveTaskEntity(Base):
    __tablename__ = "active_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    provider_task_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

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

    __table_args__ = (
        Index("idx_active_task_completed", "completed"),
        Index("idx_active_task_provider_task_id", "provider_task_id"),
    )
