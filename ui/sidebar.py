"""左侧边栏：新建对话按钮、历史对话列表、设置入口。"""

from __future__ import annotations

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
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


class _ConversationRow(QWidget):
    """对话列表行控件：左侧标题+时间，右侧垂直居中删除按钮。"""

    delete_clicked = pyqtSignal(str)

    def __init__(self, conv_id: str, title: str, time_text: str, parent: QWidget | None = None):
        super().__init__(parent)
        self._conv_id = conv_id
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(0)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        self._title_label = QLabel(title)
        self._title_label.setObjectName("convRowTitle")
        self._time_label = QLabel(time_text)
        self._time_label.setObjectName("convRowTime")

        text_layout.addWidget(self._title_label)
        text_layout.addWidget(self._time_label)
        layout.addLayout(text_layout, stretch=1)

        self._delete_btn = QPushButton("✕")
        self._delete_btn.setObjectName("deleteConvBtn")
        self._delete_btn.setFixedSize(22, 22)
        self._delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self._conv_id))
        layout.addWidget(self._delete_btn, alignment=Qt.AlignmentFlag.AlignVCenter)

        self.set_selected(False)

    def set_selected(self, selected: bool) -> None:
        if selected:
            self._title_label.setStyleSheet("color: #1A5DAB; font-weight: bold; font-size: 13px;")
            self._time_label.setStyleSheet("color: #5A8FBF; font-size: 11px;")
        else:
            self._title_label.setStyleSheet("color: #333333; font-weight: normal; font-size: 13px;")
            self._time_label.setStyleSheet("color: #999999; font-size: 11px;")


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

    def _on_item_changed(self, current: QListWidgetItem | None, previous: QListWidgetItem | None) -> None:
        if previous:
            prev_widget = self.conversation_list.itemWidget(previous)
            if isinstance(prev_widget, _ConversationRow):
                prev_widget.set_selected(False)

        if current:
            curr_widget = self.conversation_list.itemWidget(current)
            if isinstance(curr_widget, _ConversationRow):
                curr_widget.set_selected(True)
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
            self._confirm_delete(conv_id, item)

    def _on_delete_button_clicked(self, conv_id: str) -> None:
        for i in range(self.conversation_list.count()):
            item = self.conversation_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == conv_id:
                self._confirm_delete(conv_id, item)
                return

    def _confirm_delete(self, conv_id: str, item: QListWidgetItem) -> None:
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

    def add_conversation(self, conv_id: str, title: str, time_text: str, at_top: bool = True) -> None:
        item = QListWidgetItem()
        item.setData(Qt.ItemDataRole.UserRole, conv_id)

        row = _ConversationRow(conv_id, title, time_text)
        row.delete_clicked.connect(self._on_delete_button_clicked)
        item.setSizeHint(QSize(0, 52))

        if at_top:
            self.conversation_list.insertItem(0, item)
        else:
            self.conversation_list.addItem(item)

        self.conversation_list.setItemWidget(item, row)

    def update_conversation_title(self, conv_id: str, title: str) -> None:
        """更新列表中指定对话的标题显示。"""
        for i in range(self.conversation_list.count()):
            item = self.conversation_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == conv_id:
                widget = self.conversation_list.itemWidget(item)
                if isinstance(widget, _ConversationRow):
                    widget._title_label.setText(title)
                break

    def clear_conversations(self) -> None:
        self.conversation_list.clear()

    def select_conversation(self, conv_id: str) -> None:
        for i in range(self.conversation_list.count()):
            item = self.conversation_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == conv_id:
                self.conversation_list.setCurrentItem(item)
                return
