from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ProviderConfig:
    provider_name: str
    api_key: str = ""
    base_url: str = ""
    default_model: str = ""
    default_params: dict = field(default_factory=dict)
