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
    project_id: int = 0
    is_hidden: bool = False


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
    id: int
    name: str
    resolution: str  # 如 "720P"、"1080P"、"2K"、"4K"
    aspect_ratio: str  # 如 "16:9"
    created_at: int  # 13位时间戳（毫秒）
    updated_at: int  # 13位时间戳（毫秒）
    cover_image: str = ""  # 封面图路径


@dataclass
class Outline:
    id: int  # 自增ID
    project_id: int
    content: str  # 大纲文本内容
    created_at: int  # 13位时间戳（毫秒）
    updated_at: int  # 13位时间戳（毫秒）


@dataclass
class OutlineHistory:
    id: int  # 自增ID
    outline_id: int  # 指向原始大纲ID
    project_id: int
    content: str  # 历史版本的大纲内容
    created_at: int  # 13位时间戳（毫秒）


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


@dataclass
class Scene:
    """场次数据结构"""
    id: str
    script_id: int  # 所属剧本ID（整数）
    scene_number: int  # 场次号（从1开始）
    location_type: SceneLocation  # 内景/外景
    location: str  # 地点（如"审讯室"、"老城区街道"）
    time_type: SceneTime  # 时间类型（日/夜/晨/黄昏等）
    time_detail: str = ""  # 详细时间描述（可选，如"下午3点"）
    content: str = ""  # 场次具体内容（动作描述+对话）
    created_at: int = 0  # 13位时间戳（毫秒）
    updated_at: int = 0  # 13位时间戳（毫秒）


@dataclass
class Script:
    id: int  # 自增ID
    project_id: int
    title: str = ""  # 剧本标题
    created_at: int = 0  # 13位时间戳（毫秒）
    updated_at: int = 0  # 13位时间戳（毫秒）


@dataclass
class ScriptHistory:
    """剧本历史版本（快照整个剧本的所有场次）"""
    id: int  # 自增ID
    script_id: int  # 关联剧本ID（整数）
    title: str  # 剧本标题
    scenes_snapshot: str  # 所有场次的JSON快照
    created_at: int  # 13位时间戳（毫秒）


@dataclass
class Shot:
    """分镜头数据结构"""
    id: str
    scene_id: str  # 所属场次ID
    scene_number: int  # 场次号（冗余存储，方便查询）
    shot_number: int  # 分镜号（从1开始）
    design_image: str = ""  # 分镜设计图路径（可为空）
    shot_size: ShotSize = ShotSize.MEDIUM_SHOT  # 景别
    camera_movement: str = ""  # 运镜方式（如"固定"、"慢推"、"跟拍"）
    visual_content: str = ""  # 画面内容描述
    dialogue: str = ""  # 台词
    sound_effect: str = ""  # 音效
    duration: float = 0.0  # 镜头时长（秒）
    notes: str = ""  # 备注
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ShotHistory:
    """分镜历史版本（快照整个项目的所有分镜）"""
    id: str
    project_id: int  # 关联项目ID（分镜是项目级别的）
    shots_snapshot: str  # 所有分镜的JSON快照
    created_at: datetime  # 该版本创建时间


@dataclass
class Character:
    """角色数据结构"""
    id: int  # 自增ID
    uuid: str  # UUID标识
    project_id: int  # 所属项目ID
    name: str  # 角色名
    ref_code: str  # 引用代号（如 CHAR_A）
    design_image: str = ""  # 角色设计图路径（可为空）
    description: str = ""  # 形象描述
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class CharacterHistory:
    """角色编辑历史（快照单个角色的状态）"""
    id: str
    character_id: str  # 关联角色的UUID
    snapshot: str  # JSON快照（name + ref_code + description + design_image）
    created_at: datetime  # 该版本创建时间


@dataclass
class ActiveTask:
    """活跃任务记录"""
    id: int
    provider_task_id: str
    message_id: str
    provider_name: str
    model_name: str
    status: str
    completed: bool
    prompt: str
    video_url: str
    save_path: str
    error_message: str
    created_at: datetime
    updated_at: datetime
