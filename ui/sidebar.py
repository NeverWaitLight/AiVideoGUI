"""左侧边栏：新建对话按钮、历史对话列表、设置入口。"""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ui.styles import SIDEBAR_STYLE


class Sidebar(QWidget):
    """左侧边栏组件。"""

    new_conversation_clicked = pyqtSignal()
    conversation_selected = pyqtSignal(str)
    conversation_deleted = pyqtSignal(str)
    settings_clicked = pyqtSignal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(240)
        self.setStyleSheet(SIDEBAR_STYLE)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self.new_btn = QPushButton("+  新建对话")
        self.new_btn.setObjectName("newConversationBtn")
        self.new_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.new_btn.clicked.connect(self.new_conversation_clicked.emit)
        layout.addWidget(self.new_btn)

        self.conversation_list = QListWidget()
        self.conversation_list.setObjectName("conversationList")
        self.conversation_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.conversation_list.customContextMenuRequested.connect(self._on_context_menu)
        self.conversation_list.currentItemChanged.connect(self._on_item_changed)
        layout.addWidget(self.conversation_list, stretch=1)

        self.settings_btn = QPushButton("⚙  设置")
        self.settings_btn.setObjectName("settingsBtn")
        self.settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.settings_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.settings_btn.clicked.connect(self.settings_clicked.emit)

        settings_wrapper = QWidget()
        settings_wrapper.setFixedHeight(56)
        sw_layout = QVBoxLayout(settings_wrapper)
        sw_layout.setContentsMargins(0, 0, 0, 0)
        sw_layout.setSpacing(0)
        sw_layout.addWidget(self.settings_btn)
        layout.addWidget(settings_wrapper)

    def _on_item_changed(self, current: QListWidgetItem | None, _previous: QListWidgetItem | None) -> None:
        if current:
            conv_id = current.data(Qt.ItemDataRole.UserRole)
            if conv_id:
                self.conversation_selected.emit(conv_id)

    def _on_context_menu(self, pos) -> None:
        item = self.conversation_list.itemAt(pos)
        if not item:
            return
        menu = QMenu(self)
        delete_action = menu.addAction("🗑  删除对话")
        action = menu.exec(self.conversation_list.mapToGlobal(pos))
        if action == delete_action:
            conv_id = item.data(Qt.ItemDataRole.UserRole)
            if not conv_id:
                return
            reply = QMessageBox.question(
                self,
                "确认删除",
                "删除后将无法恢复该对话及其所有视频记录，是否继续？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                row = self.conversation_list.row(item)
                self.conversation_list.takeItem(row)
                self.conversation_deleted.emit(conv_id)

    def add_conversation(self, conv_id: str, title: str, time_text: str) -> None:
        item = QListWidgetItem(f"{title}\n{time_text}")
        item.setData(Qt.ItemDataRole.UserRole, conv_id)
        self.conversation_list.insertItem(0, item)

    def clear_conversations(self) -> None:
        self.conversation_list.clear()

    def select_conversation(self, conv_id: str) -> None:
        for i in range(self.conversation_list.count()):
            item = self.conversation_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == conv_id:
                self.conversation_list.setCurrentItem(item)
                return
