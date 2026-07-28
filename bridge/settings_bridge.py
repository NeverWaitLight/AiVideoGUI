"""设置桥接：Provider 配置和应用设置读写。"""

from __future__ import annotations

from loguru import logger
import os

from PySide6.QtCore import QObject, Signal, Slot

from models.provider_config import ProviderConfig
from utils import paths


class SettingsBridge(QObject):
    """设置桥接。"""

    settings_saved = Signal()

    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self._config = config_manager

    @Slot(str, result=str)
    def get_api_key(self, provider_name: str) -> str:
        cfg = self._config.get_provider(provider_name)
        return cfg.api_key if cfg else ""

    @Slot(str, result=str)
    def get_base_url(self, provider_name: str) -> str:
        cfg = self._config.get_provider(provider_name)
        return cfg.base_url if cfg else ""

    @Slot(str, result=str)
    def get_default_model(self, provider_name: str) -> str:
        cfg = self._config.get_provider(provider_name)
        return cfg.default_model if cfg else ""

    @Slot(result=str)
    def get_default_video_provider(self) -> str:
        return self._config.settings.default_provider or "dashscope"

    @Slot(result=str)
    def get_default_chat_provider(self) -> str:
        return self._config.settings.default_chat_provider or "dashscope"

    @Slot(result=str)
    def get_default_image_provider(self) -> str:
        return self._config.settings.default_image_provider or "dashscope_image"

    @Slot(str, str, str, str, str)
    def save_provider(self, provider_type: str, provider_name: str, api_key: str,
                      base_url: str, default_model: str) -> None:
        cfg = ProviderConfig(
            provider_name=provider_name,
            api_key=api_key,
            base_url=base_url,
            default_model=default_model,
        )
        self._config.upsert_provider(cfg)
        
        if provider_type == "video":
            self._config.update_settings(default_provider=provider_name)
        elif provider_type == "chat":
            self._config.update_settings(default_chat_provider=provider_name)
        elif provider_type == "image":
            self._config.update_settings(default_image_provider=provider_name)
        
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
    def get_style(self) -> str:
        """获取当前样式：Default, Fusion, Material, Universal"""
        return self._config.settings.style or "Default"

    @Slot(str)
    def set_style(self, style: str) -> None:
        """设置样式并提示需要重启"""
        if style in ("Default", "Fusion", "Material", "Universal", "Imagine"):
            self._config.update_settings(style=style)
            self.settings_saved.emit()

    @Slot(result=str)
    def get_color_scheme(self) -> str:
        """获取当前颜色方案：Light, Dark, System"""
        return self._config.settings.color_scheme or "System"

    @Slot(str)
    def set_color_scheme(self, scheme: str) -> None:
        """设置颜色方案"""
        if scheme in ("Light", "Dark", "System"):
            self._config.update_settings(color_scheme=scheme)
            self.settings_saved.emit()

