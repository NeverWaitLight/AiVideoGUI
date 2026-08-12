class ProviderConfigError(Exception):
    """Provider 配置错误基类"""
    pass


class MissingConfigError(ProviderConfigError):
    """必需配置项缺失异常"""
    def __init__(self, provider_name: str, missing_fields: list[str], config_hint: str = ""):
        self.provider_name = provider_name
        self.missing_fields = missing_fields
        fields_str = "、".join(missing_fields)

        message = f"Provider '{provider_name}' 缺少必需配置：{fields_str}\n"
        message += "\n请在设置中配置以下字段：\n"
        for field in missing_fields:
            message += f"  - {field}\n"

        if config_hint:
            message += f"\n提示：{config_hint}"

        super().__init__(message)
