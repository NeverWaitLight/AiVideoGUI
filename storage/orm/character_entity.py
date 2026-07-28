"""角色实体模型定义。"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class CharacterEntity(Base):
    """角色表。"""

    __tablename__ = "characters"

    id: Mapped[Optional[int]] = mapped_column(Integer, primary_key=True, autoincrement=True, nullable=False)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
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
    """角色编辑历史表（逐条快照，字段与 characters 表一致）。"""

    __tablename__ = "character_history"

    id: Mapped[Optional[int]] = mapped_column(Integer, primary_key=True, autoincrement=True, nullable=False)
    character_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("characters.uuid", ondelete="CASCADE"), nullable=False
    )
    project_id: Mapped[int] = mapped_column(Integer, nullable=False)

    # 角色信息（与 CharacterEntity 字段一致）
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    ref_code: Mapped[str] = mapped_column(String(100), nullable=False)
    design_image: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")

    created_at: Mapped[int] = mapped_column(Integer, nullable=False)  # 13位时间戳（毫秒）

    # 关系
    character: Mapped["CharacterEntity"] = relationship(back_populates="history")

    # 索引
    __table_args__ = (
        Index("idx_history_character", "character_id", "created_at"),
        Index("idx_character_history_project", "project_id", "created_at"),
    )
