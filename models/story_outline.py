from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StoryOutline:
    id: int  # 自增ID
    project_id: int
    content: str  # 大纲文本内容
    created_at: int  # 13位时间戳（毫秒）
    updated_at: int  # 13位时间戳（毫秒）


@dataclass
class StoryOutlineHistory:
    id: int  # 自增ID
    story_outline_id: int  # 指向原始大纲ID
    project_id: int
    content: str  # 历史版本的大纲内容
    created_at: int  # 13位时间戳（毫秒）
