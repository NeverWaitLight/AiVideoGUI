from __future__ import annotations

from dataclasses import dataclass

from models.enums import MediaType


@dataclass
class MediaFile:
    id: str
    filename: str
    media_type: MediaType
    local_path: str
    file_size: int = 0
    source: str = "task"
    conversation_id: str = ""
    message_id: str = ""
    created_at: int = 0
    thumbnail_path: str = ""
    duration: float = 0.0
    width: int = 0
    height: int = 0
    storyboard_id: int = 0
    featured: bool = False
