from dataclasses import dataclass


@dataclass
class ChatProviderPreset:
    """聊天模型厂商预设配置"""

    id: str
    display_name: str
    type: str  # "preset" 或 "custom"
    model_prefix: str
    default_model: str
    api_key_env: str
    common_models: list[str] | None = None
    description: str = ""


@dataclass
class ChatProviderCredential:
    """聊天模型厂商凭证"""

    provider_id: str
    api_key: str = ""
    base_url: str = ""  # 仅 custom 类型使用
    model: str = ""  # 仅 custom 类型使用
