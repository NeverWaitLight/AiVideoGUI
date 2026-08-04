from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ProviderConfig:
    provider_name: str
    api_key: str = ""
    base_url: str = ""
    default_model: str = ""
    default_params: dict = field(default_factory=dict)
    model_mappings: dict[str, str] = field(default_factory=dict)  # 任务类型 -> 模型名称映射（如 {"t2v": "wan2.7-t2v-2026-06-12"}）
