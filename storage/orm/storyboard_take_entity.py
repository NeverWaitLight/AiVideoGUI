from typing import Optional

from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class StoryboardTakeEntity(Base):
    __tablename__ = "storyboard_takes"

    id: Mapped[Optional[int]] = mapped_column(Integer, primary_key=True, autoincrement=True, nullable=False)
    storyboard_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("storyboard.id", ondelete="CASCADE"), nullable=False
    )
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    media_file_id: Mapped[str] = mapped_column(String(36), nullable=False, default="")
    generate_task_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("generate_tasks.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="candidate")
    comment: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_at: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        Index("idx_take_storyboard", "storyboard_id", "number"),
        Index("idx_take_generate_task", "generate_task_id"),
    )
