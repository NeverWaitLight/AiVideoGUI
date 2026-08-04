from typing import Optional

from sqlalchemy import Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class OSSFileCacheEntity(Base):
    __tablename__ = "oss_file_cache"

    id: Mapped[Optional[int]] = mapped_column(Integer, primary_key=True, autoincrement=True, nullable=False)

    local_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    oss_url: Mapped[str] = mapped_column(String(500), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)

    uploaded_at: Mapped[int] = mapped_column(Integer, nullable=False)
    expire_at: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        Index("idx_oss_cache_hash_model", "file_hash", "model_name", unique=True),
        Index("idx_oss_cache_expire", "expire_at"),
    )
