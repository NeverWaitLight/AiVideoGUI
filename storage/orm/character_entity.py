from typing import List, Optional

from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class CharacterEntity(Base):
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
    voice_tone: Mapped[str] = mapped_column(Text, nullable=False, default="")
    voice_reference_file: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_at: Mapped[int] = mapped_column(Integer, nullable=False)

    project: Mapped["ProjectEntity"] = relationship(back_populates="characters")
    history: Mapped[List["CharacterHistoryEntity"]] = relationship(
        back_populates="character", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_character_project", "project_id"),
        Index("idx_character_ref_code", "project_id", "ref_code"),
    )


class CharacterHistoryEntity(Base):
    __tablename__ = "character_history"

    id: Mapped[Optional[int]] = mapped_column(Integer, primary_key=True, autoincrement=True, nullable=False)
    character_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("characters.uuid", ondelete="CASCADE"), nullable=False
    )
    project_id: Mapped[int] = mapped_column(Integer, nullable=False)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    ref_code: Mapped[str] = mapped_column(String(100), nullable=False)
    design_image: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    voice_tone: Mapped[str] = mapped_column(Text, nullable=False, default="")
    voice_reference_file: Mapped[str] = mapped_column(Text, nullable=False, default="")

    created_at: Mapped[int] = mapped_column(Integer, nullable=False)

    character: Mapped["CharacterEntity"] = relationship(back_populates="history")

    __table_args__ = (
        Index("idx_history_character", "character_id", "created_at"),
        Index("idx_character_history_project", "project_id", "created_at"),
    )
