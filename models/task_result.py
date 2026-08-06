from __future__ import annotations

from dataclasses import dataclass

from models.enums import TaskStatus


@dataclass
class TaskResult:
    """任务结果数据模型"""
    status: TaskStatus          # 任务状态
    video_url: str = ""         # 视频URL
    error_message: str = ""     # 错误消息
