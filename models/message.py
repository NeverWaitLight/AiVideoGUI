from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from models.enums import MessageStatus


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
