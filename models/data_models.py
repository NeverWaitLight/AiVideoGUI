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
    project_id: str = ""


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
    default_image_provider: str = ""
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
    # 视频元数据
    thumbnail_path: str = ""  # 封面图路径
    duration: float = 0.0  # 时长（秒）
    width: int = 0  # 分辨率宽度
    height: int = 0  # 分辨率高度


@dataclass
class Project:
    id: str
    name: str
    resolution: str  # 如 "1280x720"
    aspect_ratio: str  # 如 "16:9"
    created_at: datetime
    cover_image: str = ""  # 封面图路径


@dataclass
class Outline:
    id: str
    project_id: str
    content: str  # 大纲文本内容
    created_at: datetime
    updated_at: datetime


@dataclass
class OutlineHistory:
    id: str
    outline_id: str
    content: str  # 历史版本的大纲内容
    created_at: datetime  # 该版本创建时间


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


@dataclass
class Scene:
    """场次数据结构"""
    id: str
    script_id: str  # 所属剧本ID
    scene_number: int  # 场次号（从1开始）
    location_type: SceneLocation  # 内景/外景
    location: str  # 地点（如"审讯室"、"老城区街道"）
    time_type: SceneTime  # 时间类型（日/夜/晨/黄昏等）
    time_detail: str = ""  # 详细时间描述（可选，如"下午3点"）
    content: str = ""  # 场次具体内容（动作描述+对话）
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Script:
    id: str
    project_id: str
    title: str = ""  # 剧本标题
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ScriptHistory:
    """剧本历史版本（快照整个剧本的所有场次）"""
    id: str
    script_id: str
    title: str  # 剧本标题
    scenes_snapshot: str  # 所有场次的JSON快照
    created_at: datetime  # 该版本创建时间
