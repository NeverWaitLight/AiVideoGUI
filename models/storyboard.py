from __future__ import annotations

from dataclasses import dataclass

from models.enums import ShotSize


@dataclass
class Storyboard:
    """分镜头数据结构"""
    scene_number: int  # 场次号（冗余存储，方便查询）
    shot_number: int  # 分镜号（从1开始）
    id: int = 0  # 自增 ID（创建时由数据库生成）
    scene_id: int = 0  # 所属场次ID（整数，关联 screenplay.id）
    design_image: str = ""  # 分镜设计图路径（可为空）
    shot_size: ShotSize = ShotSize.MEDIUM_SHOT  # 景别
    camera_movement: str = ""  # 运镜方式（如"固定"、"慢推"、"跟拍"）
    visual_content: str = ""  # 画面内容描述
    dialogue: str = ""  # 台词
    sound_effect: str = ""  # 音效
    duration: float = 0.0  # 镜头时长（秒）
    notes: str = ""  # 备注
    created_at: int = 0  # 13位时间戳（毫秒）
    updated_at: int = 0  # 13位时间戳（毫秒）


@dataclass
class StoryboardHistory:
    """分镜历史版本（逐条快照，字段与 Storyboard 一致）"""
    id: int  # 自增ID
    storyboard_id: int  # 指向原始分镜ID
    project_id: int  # 关联项目ID
    scene_id: int  # 所属场次ID
    scene_number: int  # 场次号
    shot_number: int  # 分镜号
    design_image: str = ""  # 分镜设计图路径
    shot_size: ShotSize = ShotSize.MEDIUM_SHOT  # 景别
    camera_movement: str = ""  # 运镜方式
    visual_content: str = ""  # 画面内容描述
    dialogue: str = ""  # 台词
    sound_effect: str = ""  # 音效
    duration: float = 0.0  # 镜头时长（秒）
    notes: str = ""  # 备注
    created_at: int = 0  # 13位时间戳（毫秒）
