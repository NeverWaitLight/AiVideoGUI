from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class OssConfig:
    provider_id: str
    get_policy_url: str = ""
    get_policy_params: dict[str, str] = field(default_factory=dict)
