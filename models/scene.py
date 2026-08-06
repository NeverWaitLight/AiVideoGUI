from __future__ import annotations

from dataclasses import dataclass

from models.enums import SceneLocation, SceneTime


@dataclass
class Scene:
    id: int
    project_id: int
    scene_number: int
    location_type: SceneLocation
    location: str
    time_type: SceneTime
    time_detail: str = ""
    content: str = ""
    sound_effect: str = ""     # 音效（文字描述）
    ambient_sound: str = ""    # 环境音（文字描述）
    background_music: str = "" # 背景音乐（文字描述）
    created_at: int = 0
    updated_at: int = 0


@dataclass
class ScreenplayHistory:
    id: int
    screenplay_id: int
    project_id: int
    scene_number: int
    location_type: SceneLocation
    location: str
    time_type: SceneTime
    time_detail: str = ""
    content: str = ""
    sound_effect: str = ""     # 音效（文字描述）
    ambient_sound: str = ""    # 环境音（文字描述）
    background_music: str = "" # 背景音乐（文字描述）
    created_at: int = 0
