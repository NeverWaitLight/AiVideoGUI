"""剧本实体模型定义。"""

from typing import List, Optional

from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class ScreenplayEntity(Base):
    """剧本场次表（一场戏一条记录）。"""

    __tablename__ = "screenplay"

    # 主键
    id: Mapped[Optional[int]] = mapped_column(Integer, primary_key=True, autoincrement=True, nullable=False)

    # 项目关联
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )

    # 场次信息
    scene_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # 地点信息
    location_type: Mapped[str] = mapped_column(String(50), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)

    # 时间信息
    time_type: Mapped[str] = mapped_column(String(50), nullable=False)
    time_detail: Mapped[str] = mapped_column(String(100), nullable=False, default="")

    # 场次内容
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # 时间戳
    created_at: Mapped[int] = mapped_column(Integer, nullable=False)  # 13位时间戳（毫秒）
    updated_at: Mapped[int] = mapped_column(Integer, nullable=False)  # 13位时间戳（毫秒）

    # 关系
    project: Mapped["ProjectEntity"] = relationship(back_populates="screenplays")
    storyboards: Mapped[List["StoryboardEntity"]] = relationship(
        back_populates="scene", cascade="all, delete-orphan"
    )
    history: Mapped[List["ScreenplayHistoryEntity"]] = relationship(
        back_populates="screenplay", cascade="all, delete-orphan"
    )

    # 索引
    __table_args__ = (
        Index("idx_screenplay_project", "project_id"),
        Index("idx_screenplay_project_scene", "project_id", "scene_number"),
    )


class ScreenplayHistoryEntity(Base):
    """剧本历史表（逐场次快照，字段与 screenplay 表一致）。"""

    __tablename__ = "screenplay_history"

    id: Mapped[Optional[int]] = mapped_column(Integer, primary_key=True, autoincrement=True, nullable=False)
    screenplay_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("screenplay.id", ondelete="CASCADE"), nullable=False
    )
    project_id: Mapped[int] = mapped_column(Integer, nullable=False)

    # 场次信息（与 ScreenplayEntity 字段一致）
    scene_number: Mapped[int] = mapped_column(Integer, nullable=False)
    location_type: Mapped[str] = mapped_column(String(50), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    time_type: Mapped[str] = mapped_column(String(50), nullable=False)
    time_detail: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")

    created_at: Mapped[int] = mapped_column(Integer, nullable=False)  # 13位时间戳（毫秒）

    # 关系
    screenplay: Mapped["ScreenplayEntity"] = relationship(back_populates="history")

    # 索引
    __table_args__ = (Index("idx_screenplay_history_screenplay", "screenplay_id", "created_at"),)
