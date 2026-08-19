import json
import os
from typing import TYPE_CHECKING

from loguru import logger

from models.app_settings import AppSettings
from models.oss_config import OssConfig
from models.provider_config import ProviderConfig

if TYPE_CHECKING:
    from config.providers_catalog import ProvidersCatalog


class ConfigManager:
    def __init__(
        self,
        config_path: str,
        providers_catalog: "ProvidersCatalog | None" = None,
    ) -> None:
        self._path = config_path
        self._catalog = providers_catalog
        self._providers: dict[str, ProviderConfig] = {}
        self._settings = AppSettings()
        self._load()

    @staticmethod
    def _copy_provider_config(cfg: ProviderConfig, **overrides) -> ProviderConfig:
        data = {
            "provider_name": cfg.provider_name,
            "api_key": cfg.api_key,
            "base_url": cfg.base_url,
            "submit_base_url": cfg.submit_base_url,
            "task_base_url": cfg.task_base_url,
            "default_model": cfg.default_model,
            "default_params": cfg.default_params,
            "model_mappings": cfg.model_mappings,
            "oss": cfg.oss,
        }
        data.update(overrides)
        return ProviderConfig(**data)

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
        _image_setting_renamed = {
            "bailian": "dashscope",
            "bailian_image": "dashscope",
            "dashscope_image": "dashscope",
        }
        migrated = False

        for item in data.get("providers", []):
            name = item.get("provider_name", "")
            name = _renamed.get(name, name)
            model_mappings = item.get("model_mappings", {})

            if name.endswith("_video") or name == "dashscope":
                if not model_mappings and item.get("default_model"):
                    default_model = item.get("default_model", "")
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
                submit_base_url=item.get("submit_base_url", ""),
                task_base_url=item.get("task_base_url", ""),
                default_model=item.get("default_model", ""),
                default_params=item.get("default_params", {}),
                model_mappings=model_mappings,
            )
            if cfg.provider_name and cfg.provider_name not in self._providers:
                self._providers[cfg.provider_name] = cfg

        s = data.get("app_settings", {})
        raw_image_provider = s.get("default_image_provider", "")
        image_provider = _image_setting_renamed.get(raw_image_provider, raw_image_provider)
        if image_provider != raw_image_provider:
            migrated = True
        self._settings = AppSettings(
            default_provider=_renamed.get(s.get("default_provider", ""), s.get("default_provider", "")),
            default_chat_provider=_renamed.get(s.get("default_chat_provider", ""), s.get("default_chat_provider", "")),
            default_image_provider=image_provider,
            workspace_dir=s.get("workspace_dir", ""),
            color_scheme=s.get("color_scheme", "System"),
            ignored_update_version=s.get("ignored_update_version", ""),
            close_window_action=s.get("close_window_action", ""),
        )
        logger.info(f"配置已加载，providers={list(self._providers.keys())}")

        if migrated:
            self.save()

    def save(self) -> None:
        data = {
            "providers": [
                {
                    "provider_name": p.provider_name,
                    "api_key": p.api_key,
                    "base_url": p.base_url,
                    "submit_base_url": p.submit_base_url,
                    "task_base_url": p.task_base_url,
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
                "ignored_update_version": self._settings.ignored_update_version,
                "close_window_action": self._settings.close_window_action,
            },
        }
        os.makedirs(os.path.dirname(self._path), exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_provider(self, name: str) -> ProviderConfig | None:
        return self._providers.get(name)

    @staticmethod
    def _typed_name(name: str, provider_type: str) -> str:
        if provider_type == "video" and not name.endswith("_video"):
            return f"{name}_video"
        if provider_type == "chat" and not name.endswith("_chat"):
            return f"{name}_chat"
        if provider_type == "image" and not name.endswith("_image"):
            return f"{name}_image"
        return name

    def get_provider_config(self, name: str, provider_type: str | None = None) -> ProviderConfig | None:
        if provider_type in ("video", "chat", "image"):
            typed = self._typed_name(name, provider_type)
            cfg = self._providers.get(typed)
            if cfg:
                return self._apply_catalog_defaults(cfg, provider_type)
            cfg = self._providers.get(name)
            if cfg:
                return self._apply_catalog_defaults(cfg, provider_type)
            return None
        return self._providers.get(name)

    @staticmethod
    def _base_provider_name(name: str, provider_type: str) -> str:
        if provider_type == "video" and name.endswith("_video"):
            return name[:-6]
        if provider_type == "chat" and name.endswith("_chat"):
            return name[:-5]
        if provider_type == "image" and name.endswith("_image"):
            return name[:-6]
        return name

    def get_oss_config(self, provider_id: str) -> OssConfig | None:
        if not self._catalog:
            return None
        lookup_name = provider_id
        if provider_id.endswith("_video"):
            lookup_name = provider_id[:-6]
        return self._catalog.get_oss_config(lookup_name)

    def _apply_catalog_defaults(
        self, cfg: ProviderConfig, provider_type: str
    ) -> ProviderConfig:
        if not self._catalog:
            return cfg

        lookup_name = self._base_provider_name(cfg.provider_name, provider_type)

        if provider_type == "video":
            catalog_submit = self._catalog.get_submit_base_url("video", lookup_name)
            catalog_task = self._catalog.get_task_base_url(lookup_name)
            submit_url = cfg.base_url or cfg.submit_base_url or catalog_submit
            task_url = cfg.task_base_url or catalog_task
            oss = self.get_oss_config(lookup_name)
            if (
                submit_url == (cfg.submit_base_url or cfg.base_url)
                and task_url == cfg.task_base_url
                and oss == cfg.oss
            ):
                return cfg
            return self._copy_provider_config(
                cfg,
                base_url=submit_url,
                submit_base_url=submit_url,
                task_base_url=task_url,
                oss=oss,
            )

        if cfg.base_url:
            return cfg

        base_url = self._catalog.get_base_url(provider_type, lookup_name)
        if not base_url:
            return cfg
        return self._copy_provider_config(cfg, base_url=base_url)

    def resolve_config_for_type(self, name: str, provider_type: str) -> ProviderConfig | None:
        cfg = self.get_provider_config(name, provider_type)
        if cfg and not cfg.api_key:
            base = self._providers.get(name)
            if base and base.api_key:
                return self._copy_provider_config(
                    cfg,
                    api_key=base.api_key,
                    base_url=cfg.base_url or base.base_url,
                    submit_base_url=cfg.submit_base_url or base.submit_base_url or base.base_url,
                    task_base_url=cfg.task_base_url or base.task_base_url,
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
        typed_name = self._typed_name(cfg.provider_name, provider_type)

        if provider_type == "video" and cfg.base_url and not cfg.submit_base_url:
            cfg = self._copy_provider_config(cfg, submit_base_url=cfg.base_url)

        if not cfg.api_key:
            base = self._providers.get(cfg.provider_name)
            if base:
                cfg = self._copy_provider_config(
                    cfg,
                    provider_name=typed_name,
                    api_key=base.api_key,
                    base_url=cfg.base_url or base.base_url,
                    submit_base_url=cfg.submit_base_url or base.submit_base_url or base.base_url,
                    task_base_url=cfg.task_base_url or base.task_base_url,
                )
            else:
                cfg = self._copy_provider_config(cfg, provider_name=typed_name)
        elif typed_name != cfg.provider_name:
            cfg = self._copy_provider_config(cfg, provider_name=typed_name)

        self._providers[cfg.provider_name] = cfg
        if auto_save:
            self.save()

    def delete_provider(self, name: str, auto_save: bool = True) -> None:
        self._providers.pop(name, None)
        if self._settings.default_provider == name:
            self._settings.default_provider = ""
        if auto_save:
            self.save()

    @staticmethod
    def _non_empty_mappings(mappings: dict[str, str]) -> dict[str, str]:
        return {k: v for k, v in mappings.items() if str(v).strip()}

    def _catalog_fallback_model(self, provider_name: str, provider_type: str) -> str:
        if not self._catalog:
            return ""
        lookup_name = self._base_provider_name(provider_name, provider_type)
        task_keys = ("t2i", "i2i", "r2i") if provider_type == "image" else ("t2v", "i2v", "r2v")
        for task_key in task_keys:
            models = self._catalog.list_models_for_task(provider_type, lookup_name, task_key)
            if models:
                return models[0]
        return ""

    def _resolve_effective_model(
        self, cfg: ProviderConfig, provider_type: str
    ) -> tuple[str, dict[str, str]]:
        mappings = self._non_empty_mappings(cfg.model_mappings)
        default = cfg.default_model.strip() if cfg.default_model else ""
        if not default and mappings:
            default = next(iter(mappings.values()))
        if not default and not mappings:
            default = self._catalog_fallback_model(cfg.provider_name, provider_type)
        return default, mappings

    def validate_provider_config(self, cfg: ProviderConfig, provider_type: str) -> list[str]:
        errors = []

        if not cfg.api_key:
            errors.append("未设置 API Key")

        effective_default, effective_mappings = self._resolve_effective_model(cfg, provider_type)

        if provider_type == "video":
            effective_submit = cfg.submit_base_url or cfg.base_url
            if not effective_submit and self._catalog:
                lookup_name = self._base_provider_name(cfg.provider_name, provider_type)
                effective_submit = self._catalog.get_submit_base_url("video", lookup_name)
            if not effective_submit:
                errors.append("未设置 Base URL")

            if not effective_mappings and not effective_default:
                errors.append("未配置模型映射（model_mappings）或默认模型（default_model）")

        if provider_type == "chat":
            lookup_name = self._base_provider_name(cfg.provider_name, provider_type)
            if lookup_name == "openai":
                effective_url = cfg.base_url
                if not effective_url and self._catalog:
                    effective_url = self._catalog.get_base_url(provider_type, lookup_name)
                if not effective_url:
                    errors.append("未设置 Base URL")

        if not effective_default and not effective_mappings:
            errors.append("未选择默认模型")
            return errors

        model_lower = effective_default.lower()

        if provider_type == "video" and model_lower:
            video_keywords = ["t2v", "p2v", "r2v", "video", "wan2.7", "seedance", "cogvideo"]
            if not any(kw in model_lower for kw in video_keywords):
                errors.append(f"模型 '{effective_default}' 看起来不像视频模型（应包含 t2v/video 等关键词）")

        elif provider_type == "chat":
            invalid_keywords = ["t2v", "p2v", "r2v", "t2i", "i2i", "wan2.7", "wan2.6"]
            if any(kw in model_lower for kw in invalid_keywords):
                errors.append(f"模型 '{effective_default}' 看起来不像文本模型（包含了视频/图片生成关键词）")

        elif provider_type == "image":
            image_keywords = ["t2i", "i2i", "image", "wan2.6", "flux", "dall-e", "midjourney"]
            if not any(kw in model_lower for kw in image_keywords):
                errors.append(f"模型 '{effective_default}' 看起来不像图片模型（应包含 t2i/image 等关键词）")

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
