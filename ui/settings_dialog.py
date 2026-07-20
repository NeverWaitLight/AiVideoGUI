"""设置对话框：API Key 管理、模型选择、下载目录配置。"""

from __future__ import annotations

import logging
import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    MessageBox,
    ComboBox,
    LineEdit,
    PushButton,
    PrimaryPushButton,
    Dialog,
)

from config.manager import ConfigManager
from models.data_models import ProviderConfig
from providers.bailian_chat import BailianChatProvider

logger = logging.getLogger(__name__)

# (显示文本, provider_name)
_PROVIDER_OPTIONS: list[tuple[str, str]] = [
    ("阿里万象 (DashScope)", "dashscope"),
]

# provider_name -> 可选模型
_MODEL_OPTIONS: dict[str, list[str]] = {
    "dashscope": ["wan2.7-t2v"],
}

# ── 对话模型 ──
_CHAT_PROVIDER_OPTIONS: list[tuple[str, str]] = [
    ("阿里百炼", "bailian"),
]


class SettingsDialog(Dialog):
    """应用设置对话框。"""

    def __init__(self, config: ConfigManager, parent=None):
        super().__init__("", "", parent)
        self._config = config
        self.setWindowTitle("设置")
        self.setFixedSize(520, 680)
        self._setup_ui()
        self._load_from_config()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # ── Provider 配置 ──
        provider_layout = QFormLayout()
        provider_layout.setSpacing(12)
        provider_layout.setContentsMargins(16, 20, 16, 16)

        self.provider_combo = ComboBox()
        for display, _name in _PROVIDER_OPTIONS:
            self.provider_combo.addItem(display, userData=_name)
        self.provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        provider_layout.addRow("供应商:", self.provider_combo)

        self.api_key_input = LineEdit()
        self.api_key_input.setPlaceholderText("输入 API Key")
        self.api_key_input.setEchoMode(LineEdit.EchoMode.Password)
        provider_layout.addRow("API Key:", self.api_key_input)

        self.base_url_input = LineEdit()
        self.base_url_input.setPlaceholderText("留空使用默认地址")
        provider_layout.addRow("Base URL:", self.base_url_input)

        self.model_combo = ComboBox()
        provider_layout.addRow("默认模型:", self.model_combo)

        layout.addLayout(provider_layout)

        # ── 对话模型配置 ──
        chat_layout = QFormLayout()
        chat_layout.setSpacing(12)
        chat_layout.setContentsMargins(16, 20, 16, 16)

        self.chat_provider_combo = ComboBox()
        for display, name in _CHAT_PROVIDER_OPTIONS:
            self.chat_provider_combo.addItem(display, userData=name)
        self.chat_provider_combo.currentIndexChanged.connect(self._on_chat_provider_changed)
        chat_layout.addRow("供应商:", self.chat_provider_combo)

        self.chat_api_key_input = LineEdit()
        self.chat_api_key_input.setPlaceholderText("输入 API Key")
        self.chat_api_key_input.setEchoMode(LineEdit.EchoMode.Password)
        chat_layout.addRow("API Key:", self.chat_api_key_input)

        self.chat_base_url_input = LineEdit()
        self.chat_base_url_input.setPlaceholderText("留空使用默认地址")
        chat_layout.addRow("Base URL:", self.chat_base_url_input)

        model_row = QHBoxLayout()
        self.chat_model_combo = ComboBox()
        model_row.addWidget(self.chat_model_combo, stretch=1)

        refresh_btn = PushButton("刷新")
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.clicked.connect(self._fetch_chat_models)
        model_row.addWidget(refresh_btn)
        chat_layout.addRow("默认模型:", model_row)

        layout.addLayout(chat_layout)

        # ── 应用设置 ──
        app_layout = QFormLayout()
        app_layout.setSpacing(12)
        app_layout.setContentsMargins(16, 20, 16, 16)

        dir_row = QHBoxLayout()
        self.download_dir_input = LineEdit()
        default_dir = os.path.join(os.path.expanduser("~"), "Videos", "AI-Video-GUI")
        self.download_dir_input.setText(default_dir)
        self.download_dir_input.setPlaceholderText("选择视频下载目录")
        dir_row.addWidget(self.download_dir_input)

        browse_btn = PushButton("浏览")
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(self._browse_dir)
        dir_row.addWidget(browse_btn)

        app_layout.addRow("下载目录:", dir_row)

        # 默认 Provider
        self.default_provider_combo = ComboBox()
        for display, name in _PROVIDER_OPTIONS:
            self.default_provider_combo.addItem(display, userData=name)
        app_layout.addRow("默认供应商:", self.default_provider_combo)

        layout.addLayout(app_layout)

        layout.addStretch()

        # ── 底部按钮 ──
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = PushButton("取消")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        save_btn = PrimaryPushButton("保存")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(save_btn)

        layout.addLayout(btn_row)

        # 设置到 Dialog 的内容区
        widget = QWidget()
        widget.setLayout(layout)
        self.setContentWidget(widget)

    # ───────── 加载 ─────────

    def _load_from_config(self) -> None:
        # 默认供应商
        default_name = self._config.settings.default_provider
        if default_name:
            for i in range(self.default_provider_combo.count()):
                if self.default_provider_combo.itemData(i) == default_name:
                    self.default_provider_combo.setCurrentIndex(i)
                    break

        # 下载目录
        dd = self._config.settings.default_download_dir
        if dd:
            self.download_dir_input.setText(dd)

        # 当前视频 Provider 回填
        self._on_provider_changed(self.provider_combo.currentIndex())

        # 对话模型回填
        self._on_chat_provider_changed(self.chat_provider_combo.currentIndex())

    def _on_provider_changed(self, index: int) -> None:
        provider_name = self.provider_combo.itemData(index)
        # 回填模型
        self.model_combo.clear()
        for m in _MODEL_OPTIONS.get(provider_name, []):
            self.model_combo.addItem(m)
        # 回填已保存的凭证
        cfg = self._config.get_provider(provider_name)
        if cfg:
            self.api_key_input.setText(cfg.api_key)
            self.base_url_input.setText(cfg.base_url)
            if cfg.default_model:
                i = self.model_combo.findText(cfg.default_model)
                if i >= 0:
                    self.model_combo.setCurrentIndex(i)
        else:
            self.api_key_input.clear()
            self.base_url_input.clear()

    def _browse_dir(self) -> None:
        directory = QFileDialog.getExistingDirectory(
            self, "选择下载目录", self.download_dir_input.text()
        )
        if directory:
            self.download_dir_input.setText(directory)

    # ───────── 对话模型 ─────────

    def _on_chat_provider_changed(self, index: int) -> None:
        provider_name = self.chat_provider_combo.itemData(index)
        cfg = self._config.get_provider(provider_name)
        if cfg:
            self.chat_api_key_input.setText(cfg.api_key)
            self.chat_base_url_input.setText(cfg.base_url)
            self.chat_model_combo.clear()
            if cfg.default_model:
                self.chat_model_combo.addItem(cfg.default_model)
        else:
            self.chat_api_key_input.clear()
            self.chat_base_url_input.clear()
            self.chat_model_combo.clear()

    def _fetch_chat_models(self) -> None:
        api_key = self.chat_api_key_input.text().strip()
        if not api_key:
            w = MessageBox("缺少 API Key", "请先输入 API Key 再刷新模型列表。", self)
            w.exec()
            return

        provider_name = self.chat_provider_combo.currentData()
        base_url = self.chat_base_url_input.text().strip()
        cfg = ProviderConfig(
            provider_name=provider_name,
            api_key=api_key,
            base_url=base_url,
        )
        try:
            provider = BailianChatProvider(cfg)
            models = provider.list_available_models()
        except Exception as e:
            logger.warning("获取模型列表失败：%s", e)
            w = MessageBox("获取失败", f"无法获取模型列表：\n{e}", self)
            w.exec()
            return

        if not models:
            w = MessageBox("无可用模型", "当前账号没有可用的模型。", self)
            w.exec()
            return

        current = self.chat_model_combo.currentText()
        self.chat_model_combo.clear()
        for m in models:
            self.chat_model_combo.addItem(m)
        if current:
            i = self.chat_model_combo.findText(current)
            if i >= 0:
                self.chat_model_combo.setCurrentIndex(i)

        w = MessageBox("刷新成功", f"已获取 {len(models)} 个可用模型。", self)
        w.exec()

    # ───────── 保存 ─────────

    def _on_save(self) -> None:
        provider_name = self.provider_combo.currentData()
        api_key = self.api_key_input.text().strip()
        base_url = self.base_url_input.text().strip()
        default_model = self.model_combo.currentText()

        if not api_key:
            w = MessageBox("缺少 API Key", "请输入 API Key 后再保存。", self)
            w.exec()
            return

        # 保存视频 Provider 凭证
        self._config.upsert_provider(
            ProviderConfig(
                provider_name=provider_name,
                api_key=api_key,
                base_url=base_url,
                default_model=default_model,
                default_params={},
            )
        )

        # 保存对话模型凭证
        chat_provider_name = self.chat_provider_combo.currentData()
        chat_api_key = self.chat_api_key_input.text().strip()
        chat_base_url = self.chat_base_url_input.text().strip()
        chat_model = self.chat_model_combo.currentText()
        if chat_api_key:
            self._config.upsert_provider(
                ProviderConfig(
                    provider_name=chat_provider_name,
                    api_key=chat_api_key,
                    base_url=chat_base_url,
                    default_model=chat_model,
                    default_params={},
                )
            )

        # 保存应用设置
        download_dir = self.download_dir_input.text().strip()
        default_provider = self.default_provider_combo.currentData()
        self._config.update_settings(
            default_download_dir=download_dir,
            default_provider=default_provider,
            default_chat_provider=chat_provider_name if chat_api_key else "",
        )

        self.accept()

    def get_settings(self) -> dict:
        """保留兼容，返回当前对话框中显示的配置值。"""
        return {
            "provider_name": self.provider_combo.currentData(),
            "api_key": self.api_key_input.text().strip(),
            "base_url": self.base_url_input.text().strip(),
            "default_model": self.model_combo.currentText(),
            "download_dir": self.download_dir_input.text().strip(),
        }
