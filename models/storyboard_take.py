from __future__ import annotations

from dataclasses import dataclass

from models.enums import TakeStatus


@dataclass
class StoryboardTake:
    """分镜拍摄记录数据模型"""
    storyboard_id: int              # 关联的分镜ID
    number: int                     # 第N次拍摄
    media_file_id: str              # 关联的媒体文件ID
    id: int = 0                     # 主键ID
    status: TakeStatus = TakeStatus.CANDIDATE  # 状态
    comment: str = ""               # 备注
    created_at: int = 0             # 创建时间（毫秒时间戳）
    updated_at: int = 0             # 更新时间（毫秒时间戳）
