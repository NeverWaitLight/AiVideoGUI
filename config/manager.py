import json
from loguru import logger
import os

from models.app_settings import AppSettings
from models.provider_config import ProviderConfig

class ConfigManager:
    def __init__(self, config_path: str) -> None:
        self._path = config_path
        self._providers: dict[str, ProviderConfig] = {}
        self._settings = AppSettings()
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self._path):
            logger.info(f"配置文件不存在，使用默认值：{self._path}")
            return
        try:
            with open(self._path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            logger.error(f"读取配置失败：{e}")
            return

        _renamed = {"bailian": "dashscope", "bailian_image": "dashscope_image"}

        for item in data.get("providers", []):
            name = item.get("provider_name", "")
            name = _renamed.get(name, name)
            cfg = ProviderConfig(
                provider_name=name,
                api_key=item.get("api_key", ""),
                base_url=item.get("base_url", ""),
                default_model=item.get("default_model", ""),
                default_params=item.get("default_params", {}),
                model_mappings=item.get("model_mappings", {}),
            )
            if cfg.provider_name and cfg.provider_name not in self._providers:
                self._providers[cfg.provider_name] = cfg

        s = data.get("app_settings", {})
        self._settings = AppSettings(
            default_provider=_renamed.get(s.get("default_provider", ""), s.get("default_provider", "")),
            default_chat_provider=_renamed.get(s.get("default_chat_provider", ""), s.get("default_chat_provider", "")),
            default_image_provider=_renamed.get(s.get("default_image_provider", ""), s.get("default_image_provider", "")),
            workspace_dir=s.get("workspace_dir", ""),
            color_scheme=s.get("color_scheme", "System"),
            enable_ai_request_logging=s.get("enable_ai_request_logging", False),
        )
        logger.info(f"配置已加载，providers={list(self._providers.keys())}")

    def save(self) -> None:
        data = {
            "providers": [
                {
                    "provider_name": p.provider_name,
                    "api_key": p.api_key,
                    "base_url": p.base_url,
                    "default_model": p.default_model,
                    "default_params": p.default_params,
                    "model_mappings": p.model_mappings,
                }
                for p in self._providers.values()
            ],
            "app_settings": {
                "default_provider": self._settings.default_provider,
                "default_chat_provider": self._settings.default_chat_provider,
                "default_image_provider": self._settings.default_image_provider,
                "workspace_dir": self._settings.workspace_dir,
                "color_scheme": self._settings.color_scheme,
                "enable_ai_request_logging": self._settings.enable_ai_request_logging,
            },
        }
        os.makedirs(os.path.dirname(self._path), exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"配置已保存：{self._path}")

    def get_provider(self, name: str) -> ProviderConfig | None:
        return self._providers.get(name)

    @staticmethod
    def _typed_name(name: str, provider_type: str) -> str:
        if provider_type == "video" and not name.endswith("_video"):
            return f"{name}_video"
        if provider_type == "chat" and not name.endswith("_chat"):
            return f"{name}_chat"
        return name

    def get_provider_config(self, name: str, provider_type: str | None = None) -> ProviderConfig | None:
        """按类型查找 provider 配置，支持向后兼容。

        - video: 先查 {name}_video，回退到 {name}（旧配置）
        - chat:  先查 {name}_chat，回退到 {name}（旧配置）
        - image: 先查 {name}，回退到去掉 _image 后缀的基础配置
        - None:  直接查 {name}
        """
        if provider_type in ("video", "chat"):
            typed = self._typed_name(name, provider_type)
            cfg = self._providers.get(typed)
            if cfg:
                return cfg
            return self._providers.get(name)
        if provider_type == "image":
            cfg = self._providers.get(name)
            if cfg:
                return cfg
            if name.endswith("_image"):
                base_name = name[:-6]
                return self._providers.get(base_name)
            return None
        return self._providers.get(name)

    def resolve_config_for_type(self, name: str, provider_type: str) -> ProviderConfig | None:
        """获取指定类型的完整配置（含 API key 继承）。"""
        cfg = self.get_provider_config(name, provider_type)
        if cfg and not cfg.api_key:
            base = self._providers.get(name)
            if base and base.api_key:
                return ProviderConfig(
                    provider_name=cfg.provider_name,
                    api_key=base.api_key,
                    base_url=cfg.base_url or base.base_url,
                    default_model=cfg.default_model,
                    default_params=cfg.default_params,
                    model_mappings=cfg.model_mappings,
                )
        return cfg

    def list_providers(self) -> list[ProviderConfig]:
        return list(self._providers.values())

    def upsert_provider(self, cfg: ProviderConfig, auto_save: bool = True) -> None:
        self._providers[cfg.provider_name] = cfg
        if auto_save:
            self.save()

    def save_provider_typed(
        self, cfg: ProviderConfig, provider_type: str, auto_save: bool = True
    ) -> None:
        """按类型保存 provider 配置，自动从基础配置继承 API key。"""
        typed_name = self._typed_name(cfg.provider_name, provider_type)

        if not cfg.api_key:
            base = self._providers.get(cfg.provider_name)
            if base:
                cfg = ProviderConfig(
                    provider_name=typed_name,
                    api_key=base.api_key,
                    base_url=cfg.base_url or base.base_url,
                    default_model=cfg.default_model,
                    default_params=cfg.default_params,
                    model_mappings=cfg.model_mappings,
                )
            else:
                cfg = ProviderConfig(
                    provider_name=typed_name,
                    api_key=cfg.api_key,
                    base_url=cfg.base_url,
                    default_model=cfg.default_model,
                    default_params=cfg.default_params,
                    model_mappings=cfg.model_mappings,
                )
        elif typed_name != cfg.provider_name:
            cfg = ProviderConfig(
                provider_name=typed_name,
                api_key=cfg.api_key,
                base_url=cfg.base_url,
                default_model=cfg.default_model,
                default_params=cfg.default_params,
                model_mappings=cfg.model_mappings,
            )

        self._providers[cfg.provider_name] = cfg
        if auto_save:
            self.save()

    def delete_provider(self, name: str, auto_save: bool = True) -> None:
        self._providers.pop(name, None)
        if self._settings.default_provider == name:
            self._settings.default_provider = ""
        if auto_save:
            self.save()

    def validate_provider_config(self, cfg: ProviderConfig, provider_type: str) -> list[str]:
        """验证配置是否匹配指定类型，返回错误列表（空列表表示无错误）"""
        errors = []

        if not cfg.api_key:
            errors.append("未设置 API Key")

        if not cfg.default_model:
            errors.append("未选择默认模型")
            return errors

        model_lower = cfg.default_model.lower()

        if provider_type == "video":
            video_keywords = ["t2v", "p2v", "r2v", "video", "wan2.7", "seedance", "cogvideo"]
            if not any(kw in model_lower for kw in video_keywords):
                errors.append(f"模型 '{cfg.default_model}' 看起来不像视频模型（应包含 t2v/video 等关键词）")

        elif provider_type == "chat":
            invalid_keywords = ["t2v", "p2v", "r2v", "t2i", "i2i", "wan2.7", "wan2.6"]
            if any(kw in model_lower for kw in invalid_keywords):
                errors.append(f"模型 '{cfg.default_model}' 看起来不像文本模型（包含了视频/图片生成关键词）")

        elif provider_type == "image":
            image_keywords = ["t2i", "i2i", "image", "wan2.6", "flux", "dall-e", "midjourney"]
            if not any(kw in model_lower for kw in image_keywords):
                errors.append(f"模型 '{cfg.default_model}' 看起来不像图片模型（应包含 t2i/image 等关键词）")

        return errors

    @property
    def settings(self) -> AppSettings:
        return self._settings

    def update_settings(self, auto_save: bool = True, **kwargs) -> None:
        for k, v in kwargs.items():
            if hasattr(self._settings, k):
                setattr(self._settings, k, v)
        if auto_save:
            self.save()
