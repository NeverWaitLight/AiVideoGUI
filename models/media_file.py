from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from models.enums import MediaType


@dataclass
class MediaFile:
    id: str
    filename: str
    media_type: MediaType
    local_path: str
    file_size: int = 0
    source: str = "task"
    conversation_id: str = ""
    message_id: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    # 视频元数据
    thumbnail_path: str = ""  # 封面图路径
    duration: float = 0.0  # 时长（秒）
    width: int = 0  # 分辨率宽度
    height: int = 0  # 分辨率高度
    # 分镜关联
    storyboard_id: int = 0  # 来源分镜 ID
    featured: bool = False  # 是否为封面视频
