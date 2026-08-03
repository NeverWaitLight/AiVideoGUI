from __future__ import annotations

from dataclasses import dataclass

from models.enums import ShotSize


@dataclass
class Storyboard:
    scene_number: int
    shot_number: int
    id: int = 0
    scene_id: int = 0
    design_image: str = ""
    shot_size: ShotSize = ShotSize.MEDIUM_SHOT
    camera_movement: str = ""
    visual_content: str = ""
    dialogue: str = ""
    sound_effect: str = ""
    duration: float = 0.0
    notes: str = ""
    seed: str = ""
    created_at: int = 0
    updated_at: int = 0


@dataclass
class StoryboardHistory:
    id: int
    storyboard_id: int
    project_id: int
    scene_id: int
    scene_number: int
    shot_number: int
    design_image: str = ""
    shot_size: ShotSize = ShotSize.MEDIUM_SHOT
    camera_movement: str = ""
    visual_content: str = ""
    dialogue: str = ""
    sound_effect: str = ""
    duration: float = 0.0
    notes: str = ""
    seed: str = ""
    created_at: int = 0
