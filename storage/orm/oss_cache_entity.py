"""OSS 文件缓存实体模型定义。"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class OSSFileCacheEntity(Base):
    """OSS 文件缓存表（本地文件 -> OSS URL 映射）。"""

    __tablename__ = "oss_file_cache"

    id: Mapped[Optional[int]] = mapped_column(Integer, primary_key=True, autoincrement=True, nullable=False)

    # 本地文件标识（路径 + 文件修改时间 + 文件大小，确保唯一性）
    local_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA256 hash of (path + mtime + size)

    # OSS 信息
    oss_url: Mapped[str] = mapped_column(String(500), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)  # 文件绑定的模型

    # 时间信息
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    expire_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)  # 48 小时后过期

    # 索引
    __table_args__ = (
        Index("idx_oss_cache_hash_model", "file_hash", "model_name", unique=True),
        Index("idx_oss_cache_expire", "expire_at"),
    )
