from __future__ import annotations

from dataclasses import dataclass, field

from models.oss_config import OssConfig


@dataclass
class ProviderConfig:
    """供应商配置数据模型"""
    provider_name: str                                  # 供应商名称
    api_key: str = ""                                   # API密钥
    base_url: str = ""                                  # chat/image 完整 API 地址；video 用户 override 提交地址
    submit_base_url: str = ""                           # video 提交完整 URL
    task_base_url: str = ""                             # video 任务查询 URL 前缀
    default_model: str = ""                             # 默认模型名称
    default_params: dict = field(default_factory=dict)  # 默认参数
    model_mappings: dict[str, str] = field(default_factory=dict)  # 任务类型 -> 模型名称映射（如 {"t2v": "wan2.7-t2v-2026-06-12"}）
    oss: OssConfig | None = None                        # OSS 上传配置（video 使用）
