"""设置桥接：Provider 配置和应用设置读写。"""

from __future__ import annotations

from loguru import logger

from PySide6.QtCore import QObject, Signal, Slot


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
        return self._config.get_setting("default_video_provider", "dashscope")

    @Slot(result=str)
    def get_default_chat_provider(self) -> str:
        return self._config.get_setting("default_chat_provider", "dashscope")

    @Slot(str, str, str, str)
    def save_provider(self, provider_name: str, api_key: str,
                      base_url: str, default_model: str) -> None:
        self._config.set_provider(provider_name, {
            "api_key": api_key,
            "base_url": base_url,
            "default_model": default_model,
        })
        self.settings_saved.emit()

    @Slot(str, str)
    def save_setting(self, key: str, value: str) -> None:
        self._config.set_setting(key, value)
        self.settings_saved.emit()

    @Slot(result=str)
    def get_download_dir(self) -> str:
        return self._config.get_setting("download_dir", "")
