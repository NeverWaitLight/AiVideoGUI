from typing import List, Optional

from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class ScreenplayEntity(Base):
    __tablename__ = "screenplay"

    id: Mapped[Optional[int]] = mapped_column(Integer, primary_key=True, autoincrement=True, nullable=False)

    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )

    scene_number: Mapped[int] = mapped_column(Integer, nullable=False)

    location_type: Mapped[str] = mapped_column(String(50), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)

    time_type: Mapped[str] = mapped_column(String(50), nullable=False)
    time_detail: Mapped[str] = mapped_column(String(100), nullable=False, default="")

    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    sound_effect: Mapped[str] = mapped_column(Text, nullable=False, default="")
    ambient_sound: Mapped[str] = mapped_column(Text, nullable=False, default="")
    background_music: Mapped[str] = mapped_column(Text, nullable=False, default="")

    created_at: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_at: Mapped[int] = mapped_column(Integer, nullable=False)

    project: Mapped["ProjectEntity"] = relationship(back_populates="screenplays")
    storyboards: Mapped[List["StoryboardEntity"]] = relationship(
        back_populates="scene", cascade="all, delete-orphan"
    )
    history: Mapped[List["ScreenplayHistoryEntity"]] = relationship(
        back_populates="screenplay", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_screenplay_project", "project_id"),
        Index("idx_screenplay_project_scene", "project_id", "scene_number"),
    )


class ScreenplayHistoryEntity(Base):
    __tablename__ = "screenplay_history"

    id: Mapped[Optional[int]] = mapped_column(Integer, primary_key=True, autoincrement=True, nullable=False)
    screenplay_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("screenplay.id", ondelete="CASCADE"), nullable=False
    )
    project_id: Mapped[int] = mapped_column(Integer, nullable=False)

    scene_number: Mapped[int] = mapped_column(Integer, nullable=False)
    location_type: Mapped[str] = mapped_column(String(50), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    time_type: Mapped[str] = mapped_column(String(50), nullable=False)
    time_detail: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    sound_effect: Mapped[str] = mapped_column(Text, nullable=False, default="")
    ambient_sound: Mapped[str] = mapped_column(Text, nullable=False, default="")
    background_music: Mapped[str] = mapped_column(Text, nullable=False, default="")

    created_at: Mapped[int] = mapped_column(Integer, nullable=False)

    screenplay: Mapped["ScreenplayEntity"] = relationship(back_populates="history")

    __table_args__ = (Index("idx_screenplay_history_screenplay", "screenplay_id", "created_at"),)
