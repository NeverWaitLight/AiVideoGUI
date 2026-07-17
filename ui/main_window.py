"""主窗口：左右分栏布局，组装侧边栏和聊天区域。"""

from __future__ import annotations

import uuid
from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QSplitter,
    QWidget,
)

from ui.chat_area import ChatArea
from ui.settings_dialog import SettingsDialog
from ui.sidebar import Sidebar
from ui.styles import MAIN_WINDOW_STYLE


class MainWindow(QMainWindow):
    """应用主窗口。"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI 视频生成")
        self.setMinimumSize(960, 640)
        self.resize(1100, 700)
        self.setStyleSheet(MAIN_WINDOW_STYLE)
        self._current_conversation_id: str | None = None
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.sidebar = Sidebar()
        self.chat_area = ChatArea()

        splitter.addWidget(self.sidebar)
        splitter.addWidget(self.chat_area)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([240, 860])

        main_layout.addWidget(splitter)

    def _connect_signals(self) -> None:
        self.sidebar.new_conversation_clicked.connect(self._on_new_conversation)
        self.sidebar.conversation_selected.connect(self._on_conversation_selected)
        self.sidebar.settings_clicked.connect(self._on_settings)
        self.chat_area.message_sent.connect(self._on_message_sent)

    def _on_new_conversation(self) -> None:
        conv_id = str(uuid.uuid4())
        now = datetime.now()
        title = "新对话"
        time_text = now.strftime("%Y-%m-%d %H:%M")
        self.sidebar.add_conversation(conv_id, title, time_text)
        self.sidebar.select_conversation(conv_id)
        self._current_conversation_id = conv_id
        self.chat_area.set_header(title, "wan2.7-t2v")

    def _on_conversation_selected(self, conv_id: str) -> None:
        self._current_conversation_id = conv_id

    def _on_message_sent(self, text: str) -> None:
        if not self._current_conversation_id:
            self._on_new_conversation()

        self.chat_area.add_user_message(text)
        self.chat_area.add_ai_message("收到你的描述，正在生成视频…")
        self.chat_area.add_video_card()

    def _on_settings(self) -> None:
        dialog = SettingsDialog(self)
        dialog.exec()
