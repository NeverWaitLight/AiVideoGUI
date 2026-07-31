from typing import List, Optional

from sqlalchemy import ForeignKey, Index, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class StoryOutlineEntity(Base):
    __tablename__ = "story_outlines"

    id: Mapped[Optional[int]] = mapped_column(Integer, primary_key=True, autoincrement=True, nullable=False)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_at: Mapped[int] = mapped_column(Integer, nullable=False)

    project: Mapped["ProjectEntity"] = relationship(back_populates="story_outlines")
    history: Mapped[List["StoryOutlineHistoryEntity"]] = relationship(
        back_populates="story_outline", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("idx_story_outline_project", "project_id"),)


class StoryOutlineHistoryEntity(Base):
    __tablename__ = "story_outline_history"

    id: Mapped[Optional[int]] = mapped_column(Integer, primary_key=True, autoincrement=True, nullable=False)
    story_outline_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("story_outlines.id", ondelete="CASCADE"), nullable=False
    )
    project_id: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[int] = mapped_column(Integer, nullable=False)

    story_outline: Mapped["StoryOutlineEntity"] = relationship(back_populates="history")

    __table_args__ = (Index("idx_history_story_outline", "story_outline_id", "created_at"),)
