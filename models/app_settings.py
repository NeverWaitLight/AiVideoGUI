from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AppSettings:
    default_provider: str = ""
    default_chat_provider: str = ""
    default_image_provider: str = ""
    workspace_dir: str = ""
    color_scheme: str = "System"
