from __future__ import annotations

from dataclasses import dataclass

from models.enums import SceneLocation, SceneTime


@dataclass
class Scene:
    """场次数据结构（对应 ScreenplayEntity）"""
    id: int  # 自增ID
    project_id: int  # 所属项目ID
    scene_number: int  # 场次号（从1开始）
    location_type: SceneLocation  # 内景/外景
    location: str  # 地点（如"审讯室"、"老城区街道"）
    time_type: SceneTime  # 时间类型（日/夜/晨/黄昏等）
    time_detail: str = ""  # 详细时间描述（可选，如"下午3点"）
    content: str = ""  # 场次具体内容（动作描述+对话）
    created_at: int = 0  # 13位时间戳（毫秒）
    updated_at: int = 0  # 13位时间戳（毫秒）


@dataclass
class ScreenplayHistory:
    """剧本历史版本（逐场次快照，字段与 Scene 一致）"""
    id: int  # 自增ID
    screenplay_id: int  # 指向原始场次ID
    project_id: int  # 关联项目ID
    scene_number: int  # 场次号
    location_type: SceneLocation  # 内景/外景
    location: str  # 地点
    time_type: SceneTime  # 时间类型
    time_detail: str = ""  # 详细时间描述
    content: str = ""  # 场次内容
    created_at: int = 0  # 13位时间戳（毫秒）
