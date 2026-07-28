from __future__ import annotations

from dataclasses import dataclass

from models.enums import TaskStatus


@dataclass
class TaskResult:
    status: TaskStatus
    video_url: str = ""
    error_message: str = ""
