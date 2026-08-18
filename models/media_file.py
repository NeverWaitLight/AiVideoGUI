from __future__ import annotations

from dataclasses import dataclass

from models.enums import MediaType


@dataclass
class MediaFile:
    """媒体文件数据模型"""
    id: str                     # 主键ID（UUID）
    filename: str               # 文件名
    media_type: MediaType       # 媒体类型（video/image/audio）
    local_path: str             # 本地文件路径
    file_size: int = 0          # 文件大小（字节）
    source: str = "task"        # 来源（task/import）
    conversation_id: str = ""   # 关联的对话ID
    message_id: str = ""        # 关联的消息ID
    created_at: int = 0         # 创建时间（毫秒时间戳）
    thumbnail_path: str = ""    # 缩略图路径
    first_frame_path: str = ""  # 首帧图片相对路径
    last_frame_path: str = ""   # 末帧图片相对路径
    duration: float = 0.0       # 时长（秒，仅视频）
    width: int = 0              # 宽度（像素）
    height: int = 0             # 高度（像素）
    storyboard_id: int = 0      # 关联的分镜ID
    featured: bool = False      # 是否为精选视频
