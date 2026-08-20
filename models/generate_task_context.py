from __future__ import annotations

from dataclasses import dataclass

from models.enums import GenerateTaskCallerType
from storage.session_manager import SessionManager


@dataclass
class GenerateTaskContext:
    session_manager: SessionManager
    parent_ids: str = ""
    caller_type: GenerateTaskCallerType | None = None
    caller_id: str = ""
    project_id: int | None = None
    project_name: str | None = None
    module: str = "storyboard"
    context: str | None = None
    local_path: str = ""
