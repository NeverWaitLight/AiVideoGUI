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
    """场景内外景类型"""
    INTERIOR = "interior"  # 内景
    EXTERIOR = "exterior"  # 外景
    INTERIOR_EXTERIOR = "interior_exterior"  # 内景/外景


class SceneTime(enum.Enum):
    """场景时间类型"""
    DAY = "day"  # 日
    NIGHT = "night"  # 夜
    DAWN = "dawn"  # 晨/黎明
    DUSK = "dusk"  # 黄昏/傍晚
    EVENING = "evening"  # 傍晚
    CUSTOM = "custom"  # 自定义


class ShotSize(enum.Enum):
    """景别类型"""
    EXTREME_CLOSE_UP = "extreme_close_up"  # 特写
    CLOSE_UP = "close_up"  # 近景
    MEDIUM_SHOT = "medium_shot"  # 中景
    FULL_SHOT = "full_shot"  # 全景
    LONG_SHOT = "long_shot"  # 远景
    EXTREME_LONG_SHOT = "extreme_long_shot"  # 大远景
