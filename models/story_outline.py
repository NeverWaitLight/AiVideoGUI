from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StoryOutline:
    """故事大纲数据模型"""
    id: int                     # 主键ID
    project_id: int             # 所属项目ID
    content: str                # 大纲内容
    created_at: int             # 创建时间（毫秒时间戳）
    updated_at: int             # 更新时间（毫秒时间戳）


@dataclass
class StoryOutlineHistory:
    """大纲历史版本数据模型"""
    id: int                     # 主键ID
    story_outline_id: int       # 原始大纲ID
    project_id: int             # 所属项目ID
    content: str                # 大纲内容
    created_at: int             # 创建时间（毫秒时间戳）
