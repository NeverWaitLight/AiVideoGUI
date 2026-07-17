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
    QPushButton,
    QVBoxLayout,
)

from ui.styles import SETTINGS_DIALOG_STYLE


class SettingsDialog(QDialog):
    """应用设置对话框。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setFixedSize(520, 480)
        self.setStyleSheet(SETTINGS_DIALOG_STYLE)
        self._setup_ui()

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
        self.provider_combo.addItems(["阿里万象 (DashScope)"])
        provider_layout.addRow("供应商:", self.provider_combo)

        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("输入 API Key")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        provider_layout.addRow("API Key:", self.api_key_input)

        self.base_url_input = QLineEdit()
        self.base_url_input.setPlaceholderText("https://dashscope.aliyuncs.com")
        self.base_url_input.setText("https://dashscope.aliyuncs.com")
        provider_layout.addRow("Base URL:", self.base_url_input)

        self.model_combo = QComboBox()
        self.model_combo.addItems(["wan2.7-t2v"])
        provider_layout.addRow("默认模型:", self.model_combo)

        provider_group.setLayout(provider_layout)
        layout.addWidget(provider_group)

        # ── 应用设置 ──
        app_group = QGroupBox("应用设置")
        app_layout = QFormLayout()
        app_layout.setSpacing(12)
        app_layout.setContentsMargins(16, 20, 16, 16)

        # 下载目录
        dir_row = QHBoxLayout()
        self.download_dir_input = QLineEdit()
        default_dir = os.path.join(
            os.path.expanduser("~"), "Videos", "AI-Video-GUI"
        )
        self.download_dir_input.setText(default_dir)
        self.download_dir_input.setPlaceholderText("选择视频下载目录")
        dir_row.addWidget(self.download_dir_input)

        browse_btn = QPushButton("浏览")
        browse_btn.setObjectName("browseBtn")
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(self._browse_dir)
        dir_row.addWidget(browse_btn)

        app_layout.addRow("下载目录:", dir_row)

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
        save_btn.clicked.connect(self.accept)
        btn_row.addWidget(save_btn)

        layout.addLayout(btn_row)

    def _browse_dir(self) -> None:
        directory = QFileDialog.getExistingDirectory(
            self, "选择下载目录", self.download_dir_input.text()
        )
        if directory:
            self.download_dir_input.setText(directory)

    def get_settings(self) -> dict:
        """返回当前对话框中填写的配置值。"""
        return {
            "provider_name": self.provider_combo.currentText(),
            "api_key": self.api_key_input.text().strip(),
            "base_url": self.base_url_input.text().strip(),
            "default_model": self.model_combo.currentText(),
            "download_dir": self.download_dir_input.text().strip(),
        }
