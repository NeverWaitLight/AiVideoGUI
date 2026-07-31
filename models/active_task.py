from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class ActiveTask:
    id: int
    provider_task_id: str
    message_id: str
    provider_name: str
    model_name: str
    status: str
    completed: bool
    request_params: str
    video_url: str
    save_path: str
    error_message: str
    storyboard_id: int
    created_at: datetime
    updated_at: datetime
