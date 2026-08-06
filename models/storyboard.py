from __future__ import annotations

from dataclasses import dataclass

from models.enums import ShotSize


@dataclass
class Storyboard:
    """分镜数据模型"""
    scene_number: int          # 场次号
    shot_number: int           # 镜号
    id: int = 0                # 主键ID
    scene_id: int = 0          # 关联的场次ID
    design_image: str = ""     # 设计图路径
    shot_size: ShotSize = ShotSize.MEDIUM_SHOT  # 景别
    camera_movement: str = ""  # 运镜方式
    content: str = ""          # 分镜内容（画面描述、人物动作、场景变化、人物对话等）
    sound_effect: str = ""     # 音效（文字描述）
    ambient_sound: str = ""    # 环境音（文字描述）
    background_music: str = "" # 背景音乐（文字描述）
    duration: float = 0.0      # 时长（秒）
    notes: str = ""            # 备注
    seed: str = ""             # 随机种子
    created_at: int = 0        # 创建时间（毫秒时间戳）
    updated_at: int = 0        # 更新时间（毫秒时间戳）


@dataclass
class StoryboardHistory:
    """分镜历史版本数据模型"""
    id: int                    # 主键ID
    storyboard_id: int         # 原始分镜ID
    project_id: int            # 项目ID
    scene_id: int              # 场次ID
    scene_number: int          # 场次号
    shot_number: int           # 镜号
    design_image: str = ""     # 设计图路径
    shot_size: ShotSize = ShotSize.MEDIUM_SHOT  # 景别
    camera_movement: str = ""  # 运镜方式
    content: str = ""          # 分镜内容（画面描述、人物动作、场景变化、人物对话等）
    sound_effect: str = ""     # 音效（文字描述）
    ambient_sound: str = ""    # 环境音（文字描述）
    background_music: str = "" # 背景音乐（文字描述）
    duration: float = 0.0      # 时长（秒）
    notes: str = ""            # 备注
    seed: str = ""             # 随机种子
    created_at: int = 0        # 创建时间（毫秒时间戳）
