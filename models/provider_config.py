from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ProviderConfig:
    """供应商配置数据模型"""
    provider_name: str                                  # 供应商名称
    api_key: str = ""                                   # API密钥
    base_url: str = ""                                  # API基础URL
    default_model: str = ""                             # 默认模型名称
    default_params: dict = field(default_factory=dict)  # 默认参数
    model_mappings: dict[str, str] = field(default_factory=dict)  # 任务类型 -> 模型名称映射（如 {"t2v": "wan2.7-t2v-2026-06-12"}）
