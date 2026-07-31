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
    created_at: int = 0
