"""JSON 配置文件管理。"""

import json
from loguru import logger
import os

from models.app_settings import AppSettings
from models.provider_config import ProviderConfig

class ConfigManager:
    """读写应用配置和 Provider 凭证。"""

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
                }
                for p in self._providers.values()
            ],
            "app_settings": {
                "default_provider": self._settings.default_provider,
                "default_chat_provider": self._settings.default_chat_provider,
                "default_image_provider": self._settings.default_image_provider,
                "workspace_dir": self._settings.workspace_dir,
                "color_scheme": self._settings.color_scheme,
            },
        }
        os.makedirs(os.path.dirname(self._path), exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"配置已保存：{self._path}")

    # ---------- providers ----------

    def get_provider(self, name: str) -> ProviderConfig | None:
        return self._providers.get(name)

    def list_providers(self) -> list[ProviderConfig]:
        return list(self._providers.values())

    def upsert_provider(self, cfg: ProviderConfig) -> None:
        self._providers[cfg.provider_name] = cfg
        self.save()

    def delete_provider(self, name: str) -> None:
        self._providers.pop(name, None)
        if self._settings.default_provider == name:
            self._settings.default_provider = ""
        self.save()

    # ---------- settings ----------

    @property
    def settings(self) -> AppSettings:
        return self._settings

    def update_settings(self, **kwargs) -> None:
        for k, v in kwargs.items():
            if hasattr(self._settings, k):
                setattr(self._settings, k, v)
        self.save()
