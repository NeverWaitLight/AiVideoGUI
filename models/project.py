from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Project:
    id: int
    name: str
    resolution: str  # 如 "720P"、"1080P"、"2K"、"4K"
    aspect_ratio: str  # 如 "16:9"
    created_at: int  # 13位时间戳（毫秒）
    updated_at: int  # 13位时间戳（毫秒）
    cover_image: str = ""  # 封面图路径
