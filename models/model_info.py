from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ModelInfo:
    """模型信息数据模型"""
    name: str                                          # 模型名称
    provider_name: str                                 # 供应商名称
    supported_resolutions: list[str] = field(default_factory=list)  # 支持的分辨率列表
    supported_ratios: list[str] = field(default_factory=list)       # 支持的宽高比列表
    max_duration: int = 0                              # 最大时长（秒）
    description: str = ""                              # 模型描述
