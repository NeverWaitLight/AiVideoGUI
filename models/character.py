from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Character:
    id: int
    uuid: str
    project_id: int
    name: str
    ref_code: str
    design_image: str = ""
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


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
