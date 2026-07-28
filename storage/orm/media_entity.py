"""素材文件实体模型定义。"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class MediaFileEntity(Base):
    """素材文件表。"""

    __tablename__ = "media_files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    media_type: Mapped[str] = mapped_column(String(20), nullable=False)
    local_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="task")
    conversation_id: Mapped[str] = mapped_column(String(36), nullable=False, default="")
    message_id: Mapped[str] = mapped_column(String(36), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # 视频元数据
    thumbnail_path: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    duration: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    width: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    height: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # 分镜关联（可选，标识视频来源于哪个分镜）
    storyboard_id: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    featured: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # 索引
    __table_args__ = (
        Index("idx_media_type", "media_type"),
        Index("idx_media_created", "created_at"),
        Index("idx_media_storyboard", "storyboard_id"),
    )
