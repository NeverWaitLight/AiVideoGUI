from typing import List, Optional

from sqlalchemy import Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class StoryboardEntity(Base):
    __tablename__ = "storyboard"

    id: Mapped[Optional[int]] = mapped_column(Integer, primary_key=True, autoincrement=True, nullable=False)
    scene_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("screenplay.id", ondelete="CASCADE"), nullable=False
    )
    scene_number: Mapped[int] = mapped_column(Integer, nullable=False)
    shot_number: Mapped[int] = mapped_column(Integer, nullable=False)
    design_image: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    shot_size: Mapped[str] = mapped_column(String(50), nullable=False, default="medium_shot")
    camera_movement: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    sound_effect: Mapped[str] = mapped_column(Text, nullable=False, default="")
    ambient_sound: Mapped[str] = mapped_column(Text, nullable=False, default="")
    background_music: Mapped[str] = mapped_column(Text, nullable=False, default="")
    duration: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    seed: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    created_at: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_at: Mapped[int] = mapped_column(Integer, nullable=False)

    scene: Mapped["ScreenplayEntity"] = relationship(back_populates="storyboards")
    history: Mapped[List["StoryboardHistoryEntity"]] = relationship(
        back_populates="storyboard", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_storyboard_scene", "scene_id", "shot_number"),
        Index("idx_storyboard_scene_number", "scene_number"),
    )


class StoryboardHistoryEntity(Base):
    __tablename__ = "storyboard_history"

    id: Mapped[Optional[int]] = mapped_column(Integer, primary_key=True, autoincrement=True, nullable=False)
    storyboard_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("storyboard.id", ondelete="CASCADE"), nullable=False
    )
    project_id: Mapped[int] = mapped_column(Integer, nullable=False)

    scene_id: Mapped[int] = mapped_column(Integer, nullable=False)
    scene_number: Mapped[int] = mapped_column(Integer, nullable=False)
    shot_number: Mapped[int] = mapped_column(Integer, nullable=False)
    design_image: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    shot_size: Mapped[str] = mapped_column(String(50), nullable=False, default="medium_shot")
    camera_movement: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    sound_effect: Mapped[str] = mapped_column(Text, nullable=False, default="")
    ambient_sound: Mapped[str] = mapped_column(Text, nullable=False, default="")
    background_music: Mapped[str] = mapped_column(Text, nullable=False, default="")
    duration: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    seed: Mapped[str] = mapped_column(String(255), nullable=False, default="")

    created_at: Mapped[int] = mapped_column(Integer, nullable=False)

    storyboard: Mapped["StoryboardEntity"] = relationship(back_populates="history")

    __table_args__ = (
        Index("idx_storyboard_history_storyboard", "storyboard_id", "created_at"),
        Index("idx_storyboard_history_project", "project_id", "created_at"),
    )
