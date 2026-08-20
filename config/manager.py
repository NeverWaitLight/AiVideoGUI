import json
import os
from typing import TYPE_CHECKING

from loguru import logger

from config.url_resolver import (
    has_url_template,
    normalize_host,
    resolve_url_template,
)
from models.app_settings import AppSettings
from models.oss_config import OssConfig
from models.provider_config import ProviderConfig

if TYPE_CHECKING:
    from config.providers_catalog import ProvidersCatalog

_PROVIDER_TYPES = ("chat", "image", "video")

_LEGACY_RENAMED = {"bailian": "dashscope", "bailian_image": "dashscope_image"}
_LEGACY_IMAGE_SETTING_RENAMED = {
    "bailian": "dashscope",
    "bailian_image": "dashscope",
    "dashscope_image": "dashscope",
}


class ConfigManager:
    def __init__(
        self,
        config_path: str,
        providers_catalog: "ProvidersCatalog | None" = None,
    ) -> None:
        self._path = config_path
        self._catalog = providers_catalog
        self._overrides: dict[str, dict[str, ProviderConfig]] = {
            t: {} for t in _PROVIDER_TYPES
        }
        self._settings = AppSettings()
        self._load()

    @staticmethod
    def _empty_overrides() -> dict[str, dict[str, ProviderConfig]]:
        return {t: {} for t in _PROVIDER_TYPES}

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

    @staticmethod
    def _provider_from_item(item: dict) -> ProviderConfig | None:
        provider_id = str(item.get("id") or item.get("provider_name", "")).strip()
        if not provider_id:
            return None
        model_mappings = item.get("model_mappings", {})
        if not isinstance(model_mappings, dict):
            model_mappings = {}
        default_params = item.get("default_params", {})
        if not isinstance(default_params, dict):
            default_params = {}
        return ProviderConfig(
            provider_name=provider_id,
            api_key=str(item.get("api_key", "") or ""),
            base_url=str(item.get("base_url", "") or ""),
            submit_base_url=str(item.get("submit_base_url", "") or ""),
            task_base_url=str(item.get("task_base_url", "") or ""),
            default_model=str(item.get("default_model", "") or ""),
            default_params=default_params,
            model_mappings=model_mappings,
        )

    @staticmethod
    def _serialize_provider(cfg: ProviderConfig) -> dict:
        item: dict = {"id": cfg.provider_name}
        if cfg.api_key:
            item["api_key"] = cfg.api_key
        if cfg.base_url:
            item["base_url"] = cfg.base_url
        if cfg.submit_base_url:
            item["submit_base_url"] = cfg.submit_base_url
        if cfg.task_base_url:
            item["task_base_url"] = cfg.task_base_url
        if cfg.default_model:
            item["default_model"] = cfg.default_model
        if cfg.default_params:
            item["default_params"] = cfg.default_params
        if cfg.model_mappings:
            item["model_mappings"] = cfg.model_mappings
        return item

    @staticmethod
    def _migrate_legacy_provider_name(name: str) -> tuple[str, str] | None:
        name = _LEGACY_RENAMED.get(name, name)
        if name.endswith("_video"):
            return "video", name[:-6]
        if name.endswith("_chat"):
            return "chat", name[:-5]
        if name.endswith("_image"):
            return "image", name[:-6]
        return None

    @staticmethod
    def _infer_legacy_provider_type(name: str, item: dict) -> str:
        model_mappings = item.get("model_mappings") or {}
        default_model = str(item.get("default_model", "") or "").lower()
        mapping_text = " ".join(str(v).lower() for v in model_mappings.values())
        combined = f"{default_model} {mapping_text}"
        if any(k in combined for k in ("t2v", "i2v", "r2v", "video", "wan2.7")):
            return "video"
        if any(k in combined for k in ("t2i", "i2i", "r2i", "wan2.6")):
            return "image"
        if item.get("submit_base_url") or item.get("task_base_url"):
            return "video"
        return "chat"

    def _load_new_format(self, data: dict) -> None:
        for provider_type in _PROVIDER_TYPES:
            type_data = data.get(provider_type, {})
            providers = type_data.get("providers", []) if isinstance(type_data, dict) else []
            if not isinstance(providers, list):
                continue
            for item in providers:
                if not isinstance(item, dict):
                    continue
                cfg = self._provider_from_item(item)
                if cfg:
                    self._overrides[provider_type][cfg.provider_name] = cfg

    def _load_legacy_format(self, data: dict) -> bool:
        migrated = False
        for item in data.get("providers", []):
            if not isinstance(item, dict):
                continue
            name = str(item.get("provider_name", "")).strip()
            if not name:
                continue
            name = _LEGACY_RENAMED.get(name, name)
            model_mappings = item.get("model_mappings", {})
            if not isinstance(model_mappings, dict):
                model_mappings = {}

            if name.endswith("_video") or name == "dashscope":
                if not model_mappings and item.get("default_model"):
                    default_model = str(item.get("default_model", "") or "")
                    if "t2v" in default_model.lower():
                        model_mappings = {
                            "t2v": "wan2.7-t2v-2026-06-12",
                            "i2v": "wan2.7-i2v-2026-04-25",
                            "r2v": "wan2.7-r2v-2026-06-12",
                        }
                        logger.info(f"自动迁移 {name} 的旧配置到 model_mappings")
                        migrated = True

            typed = self._migrate_legacy_provider_name(name)
            if typed:
                provider_type, provider_id = typed
            else:
                provider_type = self._infer_legacy_provider_type(name, item)
                provider_id = name

            cfg = ProviderConfig(
                provider_name=provider_id,
                api_key=str(item.get("api_key", "") or ""),
                base_url=str(item.get("base_url", "") or ""),
                submit_base_url=str(item.get("submit_base_url", "") or ""),
                task_base_url=str(item.get("task_base_url", "") or ""),
                default_model=str(item.get("default_model", "") or ""),
                default_params=item.get("default_params", {}) if isinstance(item.get("default_params"), dict) else {},
                model_mappings=model_mappings,
            )
            if provider_id not in self._overrides[provider_type]:
                self._overrides[provider_type][provider_id] = cfg
                migrated = True
        return migrated

    def _load_app_settings(self, data: dict) -> tuple[AppSettings, bool]:
        s = data.get("app_settings", {})
        if not isinstance(s, dict):
            s = {}
        raw_image_provider = s.get("default_image_provider", "")
        image_provider = _LEGACY_IMAGE_SETTING_RENAMED.get(raw_image_provider, raw_image_provider)
        migrated = image_provider != raw_image_provider
        settings = AppSettings(
            default_provider=_LEGACY_RENAMED.get(s.get("default_provider", ""), s.get("default_provider", "")),
            default_chat_provider=_LEGACY_RENAMED.get(
                s.get("default_chat_provider", ""), s.get("default_chat_provider", "")
            ),
            default_image_provider=image_provider,
            workspace_dir=s.get("workspace_dir", ""),
            color_scheme=s.get("color_scheme", "System"),
            ignored_update_version=s.get("ignored_update_version", ""),
            close_window_action=s.get("close_window_action", ""),
        )
        return settings, migrated

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

        migrated = False
        if isinstance(data.get("providers"), list):
            migrated = self._load_legacy_format(data) or migrated
        else:
            self._load_new_format(data)

        self._settings, settings_migrated = self._load_app_settings(data)
        migrated = migrated or settings_migrated

        summary = {
            t: list(self._overrides[t].keys()) for t in _PROVIDER_TYPES
        }
        logger.info(f"配置已加载，providers={summary}")

        if migrated:
            self.save()

    def save(self) -> None:
        data: dict = {"version": 1}
        for provider_type in _PROVIDER_TYPES:
            providers = [
                self._serialize_provider(cfg)
                for cfg in self._overrides[provider_type].values()
            ]
            if providers:
                data[provider_type] = {"providers": providers}
        data["app_settings"] = {
            "default_provider": self._settings.default_provider,
            "default_chat_provider": self._settings.default_chat_provider,
            "default_image_provider": self._settings.default_image_provider,
            "workspace_dir": self._settings.workspace_dir,
            "color_scheme": self._settings.color_scheme,
            "ignored_update_version": self._settings.ignored_update_version,
            "close_window_action": self._settings.close_window_action,
        }
        dir_name = os.path.dirname(self._path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_provider(self, name: str, provider_type: str | None = None) -> ProviderConfig | None:
        if provider_type in _PROVIDER_TYPES:
            return self._overrides[provider_type].get(name)
        for type_overrides in self._overrides.values():
            if name in type_overrides:
                return type_overrides[name]
        return None

    def get_provider_config(self, name: str, provider_type: str | None = None) -> ProviderConfig | None:
        if provider_type in _PROVIDER_TYPES:
            cfg = self._overrides[provider_type].get(name)
            if cfg:
                return self._apply_catalog_defaults(cfg, provider_type)
            return None
        return self.get_provider(name)

    def get_oss_config(self, provider_id: str) -> OssConfig | None:
        if not self._catalog:
            return None
        return self._catalog.get_oss_config(provider_id)

    def _resolve_catalog_urls(
        self,
        provider_type: str,
        lookup_name: str,
        user_base_url: str,
        cfg: ProviderConfig,
    ) -> tuple[str, str]:
        if provider_type == "video":
            catalog_submit = self._catalog.get_submit_base_url("video", lookup_name)
            catalog_task = self._catalog.get_task_base_url(lookup_name)
            if has_url_template(catalog_submit):
                user_host = normalize_host(user_base_url) if user_base_url else None
                submit_url = resolve_url_template(
                    catalog_submit, {"base_url": user_host}
                )
                task_url = resolve_url_template(catalog_task, {"base_url": user_host})
                return submit_url, task_url
            submit_url = user_base_url or cfg.submit_base_url or catalog_submit
            task_url = cfg.task_base_url or catalog_task
            return submit_url, task_url

        catalog_base = self._catalog.get_base_url(provider_type, lookup_name)
        if has_url_template(catalog_base):
            user_host = normalize_host(user_base_url) if user_base_url else None
            return resolve_url_template(catalog_base, {"base_url": user_host}), ""
        if user_base_url:
            return user_base_url, ""
        return catalog_base, ""

    def _apply_catalog_defaults(
        self, cfg: ProviderConfig, provider_type: str
    ) -> ProviderConfig:
        if not self._catalog:
            return cfg

        lookup_name = cfg.provider_name

        if provider_type == "video":
            submit_url, task_url = self._resolve_catalog_urls(
                provider_type, lookup_name, cfg.base_url, cfg
            )
            oss = self.get_oss_config(lookup_name)
            if (
                submit_url == cfg.submit_base_url
                and task_url == cfg.task_base_url
                and oss == cfg.oss
            ):
                return cfg
            return self._copy_provider_config(
                cfg,
                submit_base_url=submit_url,
                task_base_url=task_url,
                oss=oss,
            )

        if provider_type == "image":
            catalog_base = self._catalog.get_base_url(provider_type, lookup_name)
            if not catalog_base:
                return cfg
            if has_url_template(catalog_base):
                resolved, _ = self._resolve_catalog_urls(
                    provider_type, lookup_name, cfg.base_url, cfg
                )
                if resolved == cfg.base_url:
                    return cfg
                return self._copy_provider_config(cfg, base_url=resolved)
            if cfg.base_url:
                return cfg
            return self._copy_provider_config(cfg, base_url=catalog_base)

        if cfg.base_url:
            return cfg

        base_url = self._catalog.get_base_url(provider_type, lookup_name)
        if not base_url:
            return cfg
        return self._copy_provider_config(cfg, base_url=base_url)

    def resolve_config_for_type(self, name: str, provider_type: str) -> ProviderConfig | None:
        return self.get_provider_config(name, provider_type)

    def list_providers(self) -> list[ProviderConfig]:
        result: list[ProviderConfig] = []
        for type_overrides in self._overrides.values():
            result.extend(type_overrides.values())
        return result

    def upsert_provider(
        self,
        cfg: ProviderConfig,
        provider_type: str = "video",
        auto_save: bool = True,
    ) -> None:
        if provider_type not in _PROVIDER_TYPES:
            raise ValueError(f"未知的 provider_type：{provider_type}")
        self._overrides[provider_type][cfg.provider_name] = cfg
        if auto_save:
            self.save()

    def save_provider_typed(
        self, cfg: ProviderConfig, provider_type: str, auto_save: bool = True
    ) -> None:
        if provider_type not in _PROVIDER_TYPES:
            raise ValueError(f"未知的 provider_type：{provider_type}")
        self._overrides[provider_type][cfg.provider_name] = cfg
        if auto_save:
            self.save()

    def delete_provider(
        self, name: str, provider_type: str | None = None, auto_save: bool = True
    ) -> None:
        if provider_type in _PROVIDER_TYPES:
            self._overrides[provider_type].pop(name, None)
        else:
            for type_overrides in self._overrides.values():
                type_overrides.pop(name, None)
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
        task_keys = ("t2i", "i2i", "r2i") if provider_type == "image" else ("t2v", "i2v", "r2v")
        for task_key in task_keys:
            models = self._catalog.list_models_for_task(provider_type, provider_name, task_key)
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
            catalog_submit = ""
            if self._catalog:
                catalog_submit = self._catalog.get_submit_base_url("video", cfg.provider_name)
            if has_url_template(catalog_submit):
                submit_url, _ = self._resolve_catalog_urls(
                    "video", cfg.provider_name, cfg.base_url, cfg
                )
                effective_submit = submit_url
            else:
                effective_submit = cfg.submit_base_url or cfg.base_url
                if not effective_submit and self._catalog:
                    effective_submit = catalog_submit
            if not effective_submit:
                errors.append("未设置 Base URL")

            if not effective_mappings and not effective_default:
                errors.append("未配置模型映射（model_mappings）或默认模型（default_model）")

        if provider_type == "chat":
            if cfg.provider_name == "openai":
                effective_url = cfg.base_url
                if not effective_url and self._catalog:
                    effective_url = self._catalog.get_base_url(provider_type, cfg.provider_name)
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
