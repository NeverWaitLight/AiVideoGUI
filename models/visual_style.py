from __future__ import annotations

from dataclasses import dataclass


@dataclass
class VisualStyle:
    id: int
    name: str
    is_default: bool
    sample_image_path: str
    created_at: int
    updated_at: int
