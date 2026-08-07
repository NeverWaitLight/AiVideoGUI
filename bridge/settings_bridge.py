from __future__ import annotations

from loguru import logger
import os

from PySide6.QtCore import QObject, Signal, Slot

from models.provider_config import ProviderConfig
from utils import paths


class SettingsBridge(QObject):
    settings_saved = Signal()

    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self._config = config_manager

    @Slot(str, str, result=str)
    def get_api_key(self, provider_name: str, provider_type: str = "") -> str:
        cfg = self._config.resolve_config_for_type(name=provider_name, provider_type=provider_type) if provider_type else self._config.get_provider(name=provider_name)
        return cfg.api_key if cfg else ""

    @Slot(str, str, result=str)
    def get_base_url(self, provider_name: str, provider_type: str = "") -> str:
        cfg = self._config.resolve_config_for_type(name=provider_name, provider_type=provider_type) if provider_type else self._config.get_provider(name=provider_name)
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

    @Slot(str, str, str, result=list)
    def list_chat_models(self, api_key: str, base_url: str, provider_name: str) -> list:
        """已废弃：聊天模型现在使用预设配置，不再需要动态获取模型列表"""
        logger.warning("list_chat_models 已废弃，聊天模型使用预设配置")
        return []

    @Slot(result=list)
    def get_chat_provider_presets(self) -> list:
        """获取所有聊天模型厂商预设"""
        presets = self._config.get_chat_provider_presets()
        return [
            {
                "id": p.id,
                "display_name": p.display_name,
                "type": p.type,
                "model_prefix": p.model_prefix,
                "default_model": p.default_model,
                "common_models": p.common_models or [],
                "description": p.description,
            }
            for p in presets
        ]

    @Slot(result=str)
    def get_active_chat_provider_id(self) -> str:
        """获取当前激活的聊天模型厂商 ID"""
        return self._config.get_active_chat_provider_id() or "deepseek"

    @Slot(str)
    def set_active_chat_provider_id(self, provider_id: str) -> None:
        """设置当前激活的聊天模型厂商"""
        self._config.set_active_chat_provider_id(provider_id, auto_save=True)
        self.settings_saved.emit()

    @Slot(str, result="QVariantMap")
    def get_chat_provider_credential(self, provider_id: str) -> dict:
        """获取聊天模型厂商凭证"""
        cred = self._config.get_chat_provider_credential(provider_id)
        if not cred:
            return {"api_key": "", "base_url": "", "model": ""}
        return {
            "api_key": cred.api_key,
            "base_url": cred.base_url,
            "model": cred.model,
        }

    @Slot(str, str, str, str)
    def update_chat_provider_credential(
        self, provider_id: str, api_key: str, base_url: str = "", model: str = ""
    ) -> None:
        """更新聊天模型厂商凭证"""
        self._config.update_chat_provider_credential(
            provider_id=provider_id,
            api_key=api_key,
            base_url=base_url,
            model=model,
            auto_save=True,
        )
        self.settings_saved.emit()

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

    @Slot(result=bool)
    def get_enable_ai_request_logging(self) -> bool:
        return self._config.settings.enable_ai_request_logging

    @Slot(bool)
    def set_enable_ai_request_logging(self, enabled: bool) -> None:
        self._config.update_settings(enable_ai_request_logging=enabled)
        self.settings_saved.emit()

    @Slot(str, str, str, str, str, result=str)
    def validate_provider_config(
        self, provider_type: str, provider_name: str,
        api_key: str, base_url: str, default_model: str
    ) -> str:
        """验证配置，返回错误消息（空字符串表示无错误）"""
        cfg = ProviderConfig(
            provider_name=provider_name,
            api_key=api_key,
            base_url=base_url,
            default_model=default_model,
        )
        errors = self._config.validate_provider_config(cfg=cfg, provider_type=provider_type)
        return "\n".join(errors) if errors else ""

    @Slot(str, str, str, result=list)
    def list_image_models(self, api_key: str, base_url: str, provider_name: str) -> list:
        """获取图片模型列表"""
        if not provider_name:
            return []
        try:
            cfg = ProviderConfig(
                provider_name=provider_name,
                api_key=api_key or "dummy",
                base_url=base_url,
                default_model="",
            )

            if provider_name == "dashscope_image" or provider_name == "dashscope":
                from providers.dashscope_image import DashScopeImageProvider
                provider = DashScopeImageProvider(config=cfg)
            else:
                logger.warning(f"未知的图片供应商：{provider_name}")
                return []

            return provider.list_available_models()
        except Exception as e:
            logger.warning(f"获取图片模型列表失败：{e}")
            return []

