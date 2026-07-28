"""故事大纲实体模型定义。"""

from typing import List, Optional

from sqlalchemy import ForeignKey, Index, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class StoryOutlineEntity(Base):
    """故事大纲表。"""

    __tablename__ = "story_outlines"

    id: Mapped[Optional[int]] = mapped_column(Integer, primary_key=True, autoincrement=True, nullable=False)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[int] = mapped_column(Integer, nullable=False)  # 13位时间戳（毫秒）
    updated_at: Mapped[int] = mapped_column(Integer, nullable=False)  # 13位时间戳（毫秒）

    # 关系
    project: Mapped["ProjectEntity"] = relationship(back_populates="story_outlines")
    history: Mapped[List["StoryOutlineHistoryEntity"]] = relationship(
        back_populates="story_outline", cascade="all, delete-orphan"
    )

    # 索引
    __table_args__ = (Index("idx_story_outline_project", "project_id"),)


class StoryOutlineHistoryEntity(Base):
    """故事大纲历史表。"""

    __tablename__ = "story_outline_history"

    id: Mapped[Optional[int]] = mapped_column(Integer, primary_key=True, autoincrement=True, nullable=False)
    story_outline_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("story_outlines.id", ondelete="CASCADE"), nullable=False
    )
    project_id: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[int] = mapped_column(Integer, nullable=False)  # 13位时间戳（毫秒）

    # 关系
    story_outline: Mapped["StoryOutlineEntity"] = relationship(back_populates="history")

    # 索引
    __table_args__ = (Index("idx_history_story_outline", "story_outline_id", "created_at"),)
