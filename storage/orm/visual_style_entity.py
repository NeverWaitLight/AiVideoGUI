from typing import Optional

from sqlalchemy import Boolean, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class VisualStyleEntity(Base):
    __tablename__ = "visual_styles"

    id: Mapped[Optional[int]] = mapped_column(Integer, primary_key=True, autoincrement=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sample_image_path: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    created_at: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_at: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        Index("idx_visual_styles_created_at", "created_at", postgresql_ops={"created_at": "DESC"}),
        Index("idx_visual_styles_name", "name"),
    )
