from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Project:
    id: int
    name: str
    resolution: str
    aspect_ratio: str
    created_at: int
    updated_at: int
    cover_image: str = ""
    visual_style_id: Optional[int] = None
