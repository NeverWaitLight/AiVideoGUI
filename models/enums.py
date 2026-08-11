from __future__ import annotations

import enum


class GenerateTaskType(enum.Enum):
    """生成任务类型"""
    VIDEO = "video"
    IMAGE = "image"
    AUDIO = "audio"
    CHAT = "chat"


class GenerateTaskCallerType(enum.Enum):
    """生成任务调用者类型"""
    STORYBOARD = "storyboard"      # 分镜
    CHARACTER = "character"        # 角色
    COVER = "cover"                # 封面
    CHAT = "chat"                  # 聊天


class TaskStatus(enum.Enum):
    """视频生成任务状态"""
    PENDING = "pending"        # 待处理
    RUNNING = "running"        # 运行中
    SUCCEEDED = "succeeded"    # 成功
    FAILED = "failed"          # 失败


class MessageStatus(enum.Enum):
    """聊天消息状态"""
    GENERATING = "generating"      # 生成中
    DOWNLOADING = "downloading"    # 下载中
    COMPLETED = "completed"        # 已完成
    FAILED = "failed"              # 失败


class MediaType(enum.Enum):
    """媒体文件类型"""
    VIDEO = "video"    # 视频
    IMAGE = "image"    # 图片
    AUDIO = "audio"    # 音频


class SceneLocation(enum.Enum):
    """场景地点"""
    INTERIOR = "interior"                        # 内景
    EXTERIOR = "exterior"                        # 外景
    INTERIOR_EXTERIOR = "interior_exterior"      # 内外景


class SceneTime(enum.Enum):
    """场景时间"""
    DAY = "day"          # 白天
    NIGHT = "night"      # 夜晚
    DAWN = "dawn"        # 黎明
    DUSK = "dusk"        # 黄昏
    EVENING = "evening"  # 傍晚
    CUSTOM = "custom"    # 自定义


class ShotSize(enum.Enum):
    """镜头景别"""
    EXTREME_CLOSE_UP = "extreme_close_up"        # 特写
    CLOSE_UP = "close_up"                        # 近景
    MEDIUM_SHOT = "medium_shot"                  # 中景
    FULL_SHOT = "full_shot"                      # 全景
    LONG_SHOT = "long_shot"                      # 远景
    EXTREME_LONG_SHOT = "extreme_long_shot"      # 大远景
