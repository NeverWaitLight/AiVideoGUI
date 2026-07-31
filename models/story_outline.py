from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StoryOutline:
    id: int
    project_id: int
    content: str
    created_at: int
    updated_at: int


@dataclass
class StoryOutlineHistory:
    id: int
    story_outline_id: int
    project_id: int
    content: str
    created_at: int
