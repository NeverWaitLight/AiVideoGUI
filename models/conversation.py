from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Conversation:
    id: str
    title: str
    created_at: datetime
    model_name: str = ""
    provider_name: str = ""
    project_id: int = 0
    is_hidden: bool = False
