from __future__ import annotations

import enum
from dataclasses import dataclass, field, asdict
from typing import Any

from models.enums import GenerateTaskCallerType


class ImageScene(str, enum.Enum):
    STORYBOARD_DESIGN = "storyboard_design"
    CHARACTER_DESIGN = "character_design"
    PROJECT_COVER = "project_cover"


@dataclass
class ImageGenerationRequest:
    scene: ImageScene
    local_path: str
    caller_type: GenerateTaskCallerType
    caller_id: str
    project_id: int | None = None
    project_name: str | None = None
    size: str = "1696*960"
    negative_prompt: str = ""
    n: int = 1
    module: str = "storyboard"
    context: str | None = None
    content: str = ""
    shot_size: str = ""
    camera_movement: str = ""
    notes: str = ""
    character_info: str = ""
    visual_style: str = ""
    character_name: str = ""
    description: str = ""
    user_requirement: str = ""
    aspect_ratio: str = ""
    outline_content: str = ""
    cover_character_info: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    def to_request_params(self) -> dict[str, Any]:
        data = asdict(self)
        data["scene"] = self.scene.value
        data["caller_type"] = self.caller_type.value if self.caller_type else None
        return data

    @classmethod
    def from_request_params(cls, params: dict[str, Any]) -> ImageGenerationRequest:
        scene_raw = params.get("scene", ImageScene.STORYBOARD_DESIGN.value)
        scene = ImageScene(scene_raw) if isinstance(scene_raw, str) else scene_raw
        caller_raw = params.get("caller_type")
        caller_type = (
            GenerateTaskCallerType(caller_raw)
            if caller_raw
            else GenerateTaskCallerType.STORYBOARD
        )
        return cls(
            scene=scene,
            local_path=params.get("local_path", ""),
            caller_type=caller_type,
            caller_id=params.get("caller_id", ""),
            project_id=params.get("project_id"),
            project_name=params.get("project_name"),
            size=params.get("size", "1696*960"),
            negative_prompt=params.get("negative_prompt", ""),
            n=params.get("n", 1),
            module=params.get("module", "storyboard"),
            context=params.get("context"),
            content=params.get("content", ""),
            shot_size=params.get("shot_size", ""),
            camera_movement=params.get("camera_movement", ""),
            notes=params.get("notes", ""),
            character_info=params.get("character_info", ""),
            visual_style=params.get("visual_style", ""),
            character_name=params.get("character_name", ""),
            description=params.get("description", ""),
            user_requirement=params.get("user_requirement", ""),
            aspect_ratio=params.get("aspect_ratio", ""),
            outline_content=params.get("outline_content", ""),
            cover_character_info=params.get("cover_character_info", ""),
            extra=params.get("extra") or {},
        )
