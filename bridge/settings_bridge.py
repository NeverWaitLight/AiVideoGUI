from __future__ import annotations

import os

from PySide6.QtCore import QObject, Signal, Slot

from config.providers_catalog import ProvidersCatalog
from models.provider_config import ProviderConfig
from utils import paths


class SettingsBridge(QObject):
    settings_saved = Signal()

    def __init__(
        self,
        config_manager,
        providers_catalog: ProvidersCatalog,
        parent=None,
    ):
        super().__init__(parent)
        self._config = config_manager
        self._catalog = providers_catalog

    @Slot(str, result=list)
    def list_providers(self, provider_type: str) -> list:
        """返回 [{id, name}, ...]"""
        return self._catalog.list_providers(provider_type)

    @Slot(str, str, result=str)
    def get_provider_name(self, provider_type: str, provider_id: str) -> str:
        return self._catalog.get_name(provider_type, provider_id)

    @Slot(str, str, result=list)
    def list_models(self, provider_type: str, provider_id: str) -> list:
        return self._catalog.list_models(provider_type, provider_id)

    @Slot(str, str, str, result=list)
    def list_models_for_task(self, provider_type: str, provider_id: str, task_type: str) -> list:
        return self._catalog.list_models_for_task(provider_type, provider_id, task_type)

    @Slot(str, str, result=list)
    def list_video_models(self, provider_id: str, task_type: str) -> list:
        return self._catalog.list_models_for_task("video", provider_id, task_type)

    @Slot(str, str, result=list)
    def list_image_models(self, provider_id: str, task_type: str) -> list:
        return self._catalog.list_models_for_task("image", provider_id, task_type)

    @Slot(str, str, result=str)
    def get_provider_base_url(self, provider_type: str, provider_id: str) -> str:
        return self._catalog.get_base_url_default(provider_type, provider_id)

    @Slot(str, str, result=str)
    def get_api_key(self, provider_name: str, provider_type: str = "") -> str:
        cfg = self._config.resolve_config_for_type(name=provider_name, provider_type=provider_type) if provider_type else self._config.get_provider(name=provider_name)
        return cfg.api_key if cfg else ""

    @Slot(str, str, result=str)
    def get_base_url(self, provider_name: str, provider_type: str = "") -> str:
        cfg = self._config.get_provider(provider_name, provider_type or None)
        return cfg.base_url if cfg else ""

    @Slot(str, str, result=str)
    def get_default_model(self, provider_name: str, provider_type: str = "") -> str:
        cfg = self._config.resolve_config_for_type(name=provider_name, provider_type=provider_type) if provider_type else self._config.get_provider(name=provider_name)
        return cfg.default_model if cfg else ""

    @Slot(str, str, str, result=str)
    def get_model_for_task_type(self, provider_name: str, provider_type: str, task_type: str) -> str:
        """获取特定任务类型的模型配置（如 t2v/i2v/r2v）"""
        cfg = self._config.resolve_config_for_type(name=provider_name, provider_type=provider_type) if provider_type else self._config.get_provider(name=provider_name)
        if not cfg:
            return ""
        return cfg.model_mappings.get(task_type, cfg.default_model or "")

    @Slot(result=str)
    def get_default_video_provider(self) -> str:
        return self._config.settings.default_provider or "dashscope"

    @Slot(result=str)
    def get_default_chat_provider(self) -> str:
        return self._config.settings.default_chat_provider or "dashscope"

    @Slot(result=str)
    def get_default_image_provider(self) -> str:
        return self._config.settings.default_image_provider or "dashscope"

    @Slot(str, str, str, str, str)
    def save_provider(self, provider_type: str, provider_name: str, api_key: str,
                      base_url: str, default_model: str) -> None:
        cfg = ProviderConfig(
            provider_name=provider_name,
            api_key=api_key,
            base_url=base_url,
            default_model=default_model,
        )
        self._config.save_provider_typed(cfg=cfg, provider_type=provider_type, auto_save=False)

        if provider_type == "video":
            self._config.update_settings(auto_save=False, default_provider=provider_name)
        elif provider_type == "chat":
            self._config.update_settings(auto_save=False, default_chat_provider=provider_name)
        elif provider_type == "image":
            self._config.update_settings(auto_save=False, default_image_provider=provider_name)

        self._config.save()
        self.settings_saved.emit()

    @Slot(str, str, str, str, str, "QVariantMap")
    def batch_save_provider(self, provider_type: str, provider_name: str, api_key: str,
                            base_url: str, default_model: str, model_mappings: dict = None) -> None:
        cfg = ProviderConfig(
            provider_name=provider_name,
            api_key=api_key,
            base_url=base_url,
            default_model=default_model,
            model_mappings=model_mappings or {},
        )
        self._config.save_provider_typed(cfg=cfg, provider_type=provider_type, auto_save=False)

        if provider_type == "video":
            self._config.update_settings(auto_save=False, default_provider=provider_name)
        elif provider_type == "chat":
            self._config.update_settings(auto_save=False, default_chat_provider=provider_name)
        elif provider_type == "image":
            self._config.update_settings(auto_save=False, default_image_provider=provider_name)

    @Slot(str, str)
    def batch_set(self, key: str, value: str) -> None:
        self._config.update_settings(auto_save=False, **{key: value})

    @Slot(str, bool)
    def batch_set_bool(self, key: str, value: bool) -> None:
        self._config.update_settings(auto_save=False, **{key: value})

    @Slot()
    def commit_batch(self) -> None:
        self._config.save()
        self.settings_saved.emit()

    @Slot(str, str)
    def save_setting(self, key: str, value: str) -> None:
        self._config.update_settings(**{key: value})
        self.settings_saved.emit()

    @Slot(result=str)
    def get_workspace_dir(self) -> str:
        custom = self._config.settings.workspace_dir
        if custom:
            return custom
        root = paths.workspace_root()
        return paths.workspace_dir(root)

    @Slot(str)
    def set_workspace_dir(self, path: str) -> None:
        self._config.update_settings(workspace_dir=path)
        self.settings_saved.emit()

    @Slot(result=str)
    def browse_workspace_dir(self) -> str:
        from PySide6.QtWidgets import QFileDialog
        current = self.get_workspace_dir()
        path = QFileDialog.getExistingDirectory(None, "选择工作目录", current)
        return path if path else current

    @Slot(result=str)
    def get_color_scheme(self) -> str:
        return self._config.settings.color_scheme or "System"

    @Slot(str)
    def set_color_scheme(self, scheme: str) -> None:
        if scheme in ("Light", "Dark", "System"):
            self._config.update_settings(color_scheme=scheme)
            self.settings_saved.emit()

    @Slot(result=str)
    def get_close_window_action(self) -> str:
        return self._config.settings.close_window_action or ""

    @Slot(str)
    def set_close_window_action(self, action: str) -> None:
        if action in ("", "minimize", "quit"):
            self._config.update_settings(close_window_action=action)
            self.settings_saved.emit()

    @Slot(str, str, str, str, str, "QVariantMap", result=str)
    def validate_provider_config(
        self, provider_type: str, provider_name: str,
        api_key: str, base_url: str, default_model: str,
        model_mappings: dict | None = None,
    ) -> str:
        """验证配置，返回错误消息（空字符串表示无错误）"""
        mappings = model_mappings or {}
        submit_base_url = base_url if provider_type == "video" else ""
        cfg = ProviderConfig(
            provider_name=provider_name,
            api_key=api_key,
            base_url=base_url,
            submit_base_url=submit_base_url,
            default_model=default_model,
            model_mappings=mappings,
        )
        errors = self._config.validate_provider_config(cfg=cfg, provider_type=provider_type)
        return "\n".join(errors) if errors else ""
