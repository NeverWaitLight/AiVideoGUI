from __future__ import annotations

import enum


class TaskStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class MessageStatus(enum.Enum):
    GENERATING = "generating"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"


class MediaType(enum.Enum):
    VIDEO = "video"
    IMAGE = "image"
    AUDIO = "audio"


class SceneLocation(enum.Enum):
    INTERIOR = "interior"
    EXTERIOR = "exterior"
    INTERIOR_EXTERIOR = "interior_exterior"


class SceneTime(enum.Enum):
    DAY = "day"
    NIGHT = "night"
    DAWN = "dawn"
    DUSK = "dusk"
    EVENING = "evening"
    CUSTOM = "custom"


class ShotSize(enum.Enum):
    EXTREME_CLOSE_UP = "extreme_close_up"
    CLOSE_UP = "close_up"
    MEDIUM_SHOT = "medium_shot"
    FULL_SHOT = "full_shot"
    LONG_SHOT = "long_shot"
    EXTREME_LONG_SHOT = "extreme_long_shot"
