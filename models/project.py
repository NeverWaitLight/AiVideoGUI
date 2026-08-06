from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Project:
    """项目数据模型"""
    id: int                             # 主键ID
    name: str                           # 项目名称
    resolution: str                     # 分辨率（如 720P、1080P）
    aspect_ratio: str                   # 宽高比（如 16:9、9:16）
    created_at: int                     # 创建时间（毫秒时间戳）
    updated_at: int                     # 更新时间（毫秒时间戳）
    cover_image: str = ""               # 封面图路径
    visual_style_id: Optional[int] = None  # 视觉风格ID
