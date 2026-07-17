"""设置对话框：API Key 管理、模型选择、下载目录配置。"""

from __future__ import annotations

import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from config.manager import ConfigManager
from models.data_models import ProviderConfig
from ui.styles import SETTINGS_DIALOG_STYLE

# (显示文本, provider_name)
_PROVIDER_OPTIONS: list[tuple[str, str]] = [
    ("阿里万象 (DashScope)", "dashscope"),
]

# provider_name -> 可选模型
_MODEL_OPTIONS: dict[str, list[str]] = {
    "dashscope": ["wan2.7-t2v"],
}


class SettingsDialog(QDialog):
    """应用设置对话框。"""

    def __init__(self, config: ConfigManager, parent=None):
        super().__init__(parent)
        self._config = config
        self.setWindowTitle("设置")
        self.setFixedSize(520, 520)
        self.setStyleSheet(SETTINGS_DIALOG_STYLE)
        self._setup_ui()
        self._load_from_config()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # ── Provider 配置 ──
        provider_group = QGroupBox("供应商配置")
        provider_layout = QFormLayout()
        provider_layout.setSpacing(12)
        provider_layout.setContentsMargins(16, 20, 16, 16)

        self.provider_combo = QComboBox()
        for display, _name in _PROVIDER_OPTIONS:
            self.provider_combo.addItem(display, _name)
        self.provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        provider_layout.addRow("供应商:", self.provider_combo)

        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("输入 API Key")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        provider_layout.addRow("API Key:", self.api_key_input)

        self.base_url_input = QLineEdit()
        self.base_url_input.setPlaceholderText("留空使用默认地址")
        provider_layout.addRow("Base URL:", self.base_url_input)

        self.model_combo = QComboBox()
        provider_layout.addRow("默认模型:", self.model_combo)

        provider_group.setLayout(provider_layout)
        layout.addWidget(provider_group)

        # ── 应用设置 ──
        app_group = QGroupBox("应用设置")
        app_layout = QFormLayout()
        app_layout.setSpacing(12)
        app_layout.setContentsMargins(16, 20, 16, 16)

        dir_row = QHBoxLayout()
        self.download_dir_input = QLineEdit()
        default_dir = os.path.join(os.path.expanduser("~"), "Videos", "AI-Video-GUI")
        self.download_dir_input.setText(default_dir)
        self.download_dir_input.setPlaceholderText("选择视频下载目录")
        dir_row.addWidget(self.download_dir_input)

        browse_btn = QPushButton("浏览")
        browse_btn.setObjectName("browseBtn")
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(self._browse_dir)
        dir_row.addWidget(browse_btn)

        app_layout.addRow("下载目录:", dir_row)

        # 默认 Provider
        self.default_provider_combo = QComboBox()
        for display, name in _PROVIDER_OPTIONS:
            self.default_provider_combo.addItem(display, name)
        app_layout.addRow("默认供应商:", self.default_provider_combo)

        app_group.setLayout(app_layout)
        layout.addWidget(app_group)

        layout.addStretch()

        # ── 底部按钮 ──
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        save_btn = QPushButton("保存")
        save_btn.setObjectName("saveBtn")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(save_btn)

        layout.addLayout(btn_row)

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

        # 当前 Provider 回填
        self._on_provider_changed(self.provider_combo.currentIndex())

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

    # ───────── 保存 ─────────

    def _on_save(self) -> None:
        provider_name = self.provider_combo.currentData()
        api_key = self.api_key_input.text().strip()
        base_url = self.base_url_input.text().strip()
        default_model = self.model_combo.currentText()

        if not api_key:
            QMessageBox.warning(self, "缺少 API Key", "请输入 API Key 后再保存。")
            return

        # 保存 Provider 凭证
        self._config.upsert_provider(
            ProviderConfig(
                provider_name=provider_name,
                api_key=api_key,
                base_url=base_url,
                default_model=default_model,
                default_params={},
            )
        )

        # 保存应用设置
        download_dir = self.download_dir_input.text().strip()
        default_provider = self.default_provider_combo.currentData()
        self._config.update_settings(
            default_download_dir=download_dir,
            default_provider=default_provider,
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
