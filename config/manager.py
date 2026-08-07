import json
from loguru import logger
import os

from models.app_settings import AppSettings
from models.provider_config import ProviderConfig
from models.chat_provider_preset import ChatProviderPreset, ChatProviderCredential

class ConfigManager:
    def __init__(self, config_path: str) -> None:
        self._path = config_path
        self._providers: dict[str, ProviderConfig] = {}
        self._settings = AppSettings()
        self._chat_presets: list[ChatProviderPreset] = []
        self._active_chat_provider_id: str = ""
        self._chat_credentials: dict[str, ChatProviderCredential] = {}
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

        # 加载聊天模型预设配置
        self._chat_presets = []
        for item in data.get("chat_providers", []):
            preset = ChatProviderPreset(
                id=item.get("id", ""),
                display_name=item.get("display_name", ""),
                type=item.get("type", "preset"),
                model_prefix=item.get("model_prefix", ""),
                default_model=item.get("default_model", ""),
                api_key_env=item.get("api_key_env", ""),
                common_models=item.get("common_models", []),
                description=item.get("description", ""),
            )
            self._chat_presets.append(preset)

        self._active_chat_provider_id = data.get("active_provider_id", "")

        # 加载聊天模型凭证
        self._chat_credentials = {}
        for provider_id, cred_data in data.get("provider_credentials", {}).items():
            cred = ChatProviderCredential(
                provider_id=provider_id,
                api_key=cred_data.get("api_key", ""),
                base_url=cred_data.get("base_url", ""),
                model=cred_data.get("model", ""),
            )
            self._chat_credentials[provider_id] = cred

        # 加载旧的 providers 配置（视频、图片等）
        _renamed = {"bailian": "dashscope", "bailian_image": "dashscope_image"}
        migrated = False

        for item in data.get("providers", []):
            name = item.get("provider_name", "")
            name = _renamed.get(name, name)
            model_mappings = item.get("model_mappings", {})

            # 迁移旧配置：如果是视频 provider 且没有 model_mappings，从 default_model 推断
            if name.endswith("_video") or name == "dashscope":
                if not model_mappings and item.get("default_model"):
                    default_model = item.get("default_model", "")
                    # 根据 default_model 推断任务类型映射
                    if "t2v" in default_model.lower():
                        model_mappings = {
                            "t2v": "wan2.7-t2v-2026-06-12",
                            "i2v": "wan2.7-i2v-2026-04-25",
                            "r2v": "wan2.7-r2v-2026-06-12"
                        }
                        logger.info(f"自动迁移 {name} 的旧配置到 model_mappings")
                        migrated = True

            cfg = ProviderConfig(
                provider_name=name,
                api_key=item.get("api_key", ""),
                base_url=item.get("base_url", ""),
                default_model=item.get("default_model", ""),
                default_params=item.get("default_params", {}),
                model_mappings=model_mappings,
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
            enable_ai_request_logging=s.get("enable_ai_request_logging", True),
        )
        logger.info(f"配置已加载，providers={list(self._providers.keys())}, chat_presets={len(self._chat_presets)}")

        # 如果发生了迁移，自动保存更新后的配置
        if migrated:
            self.save()
            logger.info("已保存迁移后的配置")

    def save(self) -> None:
        data = {
            "chat_providers": [
                {
                    "id": p.id,
                    "display_name": p.display_name,
                    "type": p.type,
                    "model_prefix": p.model_prefix,
                    "default_model": p.default_model,
                    "api_key_env": p.api_key_env,
                    "common_models": p.common_models or [],
                    "description": p.description,
                }
                for p in self._chat_presets
            ],
            "active_provider_id": self._active_chat_provider_id,
            "provider_credentials": {
                provider_id: {
                    "api_key": cred.api_key,
                    "base_url": cred.base_url,
                    "model": cred.model,
                }
                for provider_id, cred in self._chat_credentials.items()
            },
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

    def get_chat_provider_presets(self) -> list[ChatProviderPreset]:
        """获取所有聊天模型厂商预设"""
        return self._chat_presets

    def get_active_chat_provider_id(self) -> str:
        """获取当前激活的聊天模型厂商 ID"""
        return self._active_chat_provider_id

    def set_active_chat_provider_id(self, provider_id: str, auto_save: bool = True) -> None:
        """设置当前激活的聊天模型厂商"""
        self._active_chat_provider_id = provider_id
        if auto_save:
            self.save()

    def get_chat_provider_preset(self, provider_id: str) -> ChatProviderPreset | None:
        """根据 ID 获取聊天模型厂商预设"""
        for preset in self._chat_presets:
            if preset.id == provider_id:
                return preset
        return None

    def get_chat_provider_credential(self, provider_id: str) -> ChatProviderCredential | None:
        """获取聊天模型厂商凭证"""
        return self._chat_credentials.get(provider_id)

    def update_chat_provider_credential(
        self, provider_id: str, api_key: str = "", base_url: str = "", model: str = "", auto_save: bool = True
    ) -> None:
        """更新聊天模型厂商凭证"""
        if provider_id not in self._chat_credentials:
            self._chat_credentials[provider_id] = ChatProviderCredential(provider_id=provider_id)

        cred = self._chat_credentials[provider_id]
        if api_key:
            cred.api_key = api_key
        if base_url:
            cred.base_url = base_url
        if model:
            cred.model = model

        if auto_save:
            self.save()
