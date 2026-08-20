from __future__ import annotations

import enum
from dataclasses import dataclass, field, asdict
from typing import Any

from models.enums import GenerateTaskCallerType


class VideoScene(str, enum.Enum):
    SHOT_VIDEO = "shot_video"


@dataclass
class VideoGenerationRequest:
    scene: VideoScene
    storyboard_id: int
    local_path: str
    provider_name: str
    project_id: int | None = None
    project_name: str | None = None
    scene_id: int | None = None
    prev_shot_id: int | None = None
    next_shot_id: int | None = None
    scene_number: int = 0
    shot_number: int = 0
    reference_images: list[str] = field(default_factory=list)
    reference_images_info: list[dict[str, str]] = field(default_factory=list)
    visual_style: str | None = None
    params: dict[str, Any] = field(default_factory=dict)
    prev_shot_last_frame: str = ""
    clean_prompt: bool = True
    reference_image: str = ""

    def to_request_params(self) -> dict[str, Any]:
        data = asdict(self)
        data["scene"] = self.scene.value
        return data

    @classmethod
    def from_request_params(cls, params: dict[str, Any]) -> VideoGenerationRequest:
        scene_raw = params.get("scene", VideoScene.SHOT_VIDEO.value)
        scene = VideoScene(scene_raw) if isinstance(scene_raw, str) else scene_raw
        return cls(
            scene=scene,
            storyboard_id=int(params.get("storyboard_id", 0)),
            local_path=params.get("local_path", ""),
            provider_name=params.get("provider_name", ""),
            project_id=params.get("project_id"),
            project_name=params.get("project_name"),
            scene_id=params.get("scene_id"),
            prev_shot_id=params.get("prev_shot_id"),
            next_shot_id=params.get("next_shot_id"),
            scene_number=int(params.get("scene_number", 0)),
            shot_number=int(params.get("shot_number", 0)),
            reference_images=list(params.get("reference_images") or []),
            reference_images_info=list(params.get("reference_images_info") or []),
            visual_style=params.get("visual_style"),
            params=dict(params.get("params") or {}),
            prev_shot_last_frame=params.get("prev_shot_last_frame", ""),
            clean_prompt=bool(params.get("clean_prompt", True)),
            reference_image=params.get("reference_image", ""),
        )
