from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ModelInfo:
    name: str
    provider_name: str
    supported_resolutions: list[str] = field(default_factory=list)
    supported_ratios: list[str] = field(default_factory=list)
    max_duration: int = 0
    description: str = ""
