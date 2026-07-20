from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime


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


@dataclass
class Conversation:
    id: str
    title: str
    created_at: datetime
    model_name: str = ""
    provider_name: str = ""


@dataclass
class Message:
    id: str
    conversation_id: str
    role: str  # "user" or "assistant"
    content: str
    created_at: datetime
    task_id: str = ""
    video_url: str = ""
    local_path: str = ""
    status: MessageStatus = MessageStatus.GENERATING
    error_message: str = ""


@dataclass
class ProviderConfig:
    provider_name: str
    api_key: str = ""
    base_url: str = ""
    default_model: str = ""
    default_params: dict = field(default_factory=dict)


@dataclass
class AppSettings:
    default_provider: str = ""
    default_chat_provider: str = ""
    default_download_dir: str = ""
    theme: str = "light"


@dataclass
class TaskResult:
    status: TaskStatus
    video_url: str = ""
    error_message: str = ""


@dataclass
class ModelInfo:
    name: str
    provider_name: str
    supported_resolutions: list[str] = field(default_factory=list)
    supported_ratios: list[str] = field(default_factory=list)
    max_duration: int = 0
    description: str = ""


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
    created_at: datetime = field(default_factory=datetime.now)
