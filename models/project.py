from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Project:
    id: int
    name: str
    resolution: str
    aspect_ratio: str
    created_at: int
    updated_at: int
    cover_image: str = ""
