from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Character:
    id: int
    uuid: str
    project_id: int
    name: str
    ref_code: str
    design_image: str = ""
    description: str = ""
    created_at: int = 0
    updated_at: int = 0


@dataclass
class CharacterHistory:
    id: int
    character_id: str
    project_id: int
    name: str
    ref_code: str
    design_image: str = ""
    description: str = ""
    created_at: int = 0
