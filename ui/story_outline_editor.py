"""故事大纲编辑器：支持编辑、AI 对话修改和历史版本管理。"""

from __future__ import annotations

from loguru import logger

from PyQt6.QtCore import Qt, pyqtSignal, QSize, QThread
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
    QTextEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QSplitter,
    QDialog,
    QScrollArea,
    QFrame,
)
from qfluentwidgets import (
    PrimaryPushButton,
    PushButton,
    ToolButton,
    FluentIcon,
    TextEdit,
)

from models.data_models import StoryOutline, StoryOutlineHistory
from service.story_outline_service import StoryOutlineService
from service.text_model_service import TextModelService
from ui.styles import style_button
from utils.time_formatter import format_timestamp, get_current_timestamp_ms

class OptimizeWorker(QThread):
    """AI 优化后台线程。"""

    finished = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(
        self,
        text_service: TextModelService,
        original_content: str,
        requirement: str,
        model: str,
    ):
        super().__init__()
        self._service = text_service
        self._original = original_content
        self._requirement = requirement
        self._model = model

    def run(self) -> None:
        try:
            result = self._service.optimize_story_outline(
                self._original, self._requirement, self._model
            )
            self.finished.emit(result)
        except Exception as e:
            logger.exception("AI 优化失败")
            self.failed.emit(str(e))

class HistoryListItem(QWidget):
    """历史版本列表项。"""

    restore_clicked = pyqtSignal(int)

    def __init__(self, history: StoryOutlineHistory, parent: QWidget | None = None):
        super().__init__(parent)
        self._history = history
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        time_label = QLabel(format_timestamp(self._history.created_at))
        time_label.setStyleSheet("font-size: 13px; color: #666;")
        layout.addWidget(time_label, stretch=1)

        restore_btn = PushButton("恢复")
        restore_btn.clicked.connect(lambda: self.restore_clicked.emit(self._history.id))
        layout.addWidget(restore_btn)

class HistoryDialog(QDialog):
    """历史版本弹出对话框。"""

    restore_requested = pyqtSignal(int)

    def __init__(
        self,
        story_outline_id: int,
        story_outline_service: StoryOutlineService,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._story_outline_id = story_outline_id
        self._service = story_outline_service
        self.setWindowTitle("历史版本")
        self.setFixedSize(400, 500)
        self._setup_ui()
        self._load_history()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self._list = QListWidget()
        self._list.setStyleSheet(
            """
            QListWidget {
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                background: white;
            }
            QListWidget::item {
                border-bottom: 1px solid #F0F0F0;
                padding: 0px;
            }
            QListWidget::item:hover {
                background: #F5F5F5;
            }
            QListWidget::item:selected {
                background: #E3F2FD;
            }
            """
        )
        layout.addWidget(self._list)

    def _load_history(self) -> None:
        self._list.clear()
        history_list = self._service.list_history(self._story_outline_id)

        if not history_list:
            empty_item = QListWidgetItem(self._list)
            empty_widget = QLabel("暂无历史版本")
            empty_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_widget.setStyleSheet("color: #999; padding: 20px;")
            empty_item.setSizeHint(empty_widget.sizeHint())
            self._list.addItem(empty_item)
            self._list.setItemWidget(empty_item, empty_widget)
            return

        for history in history_list:
            item = QListWidgetItem(self._list)
            widget = HistoryListItem(history)
            widget.restore_clicked.connect(self._on_restore)
            item.setSizeHint(widget.sizeHint())
            self._list.addItem(item)
            self._list.setItemWidget(item, widget)

    def _on_restore(self, history_id: str) -> None:
        self.restore_requested.emit(history_id)
        self.accept()

class _ChatBubble(QWidget):
    """轻量聊天气泡，区分用户和 AI 对齐方向。"""

    def __init__(self, role: str, text: str, parent: QWidget | None = None):
        super().__init__(parent)
        self._setup_ui(role, text)

    def _setup_ui(self, role: str, text: str) -> None:
        outer = QHBoxLayout(self)
        outer.setContentsMargins(12, 2, 12, 2)

        is_user = role == "user"

        if is_user:
            outer.addStretch(1)

        bg = "#DCF8C6" if is_user else "#FFFFFF"
        self.setMaximumWidth(400)

        frame = QFrame()
        frame.setStyleSheet(f"QFrame {{ background-color: {bg}; border-radius: 10px; }}")

        inner = QVBoxLayout(frame)
        inner.setContentsMargins(10, 8, 10, 8)

        label = QLabel(text)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        label.setStyleSheet("color: #333; background: transparent; font-size: 13px;")
        inner.addWidget(label)

        outer.addWidget(frame)

        if is_user:
            pass
        else:
            outer.addStretch(1)

class StoryOutlineChatPanel(QWidget):
    """右侧 AI 对话面板，用于通过对话修改大纲内容。"""

    content_updated = pyqtSignal(str)

    def __init__(
        self,
        text_service: TextModelService,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._text_service = text_service
        self._worker: OptimizeWorker | None = None
        self._current_content: str = ""
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QLabel("  AI 助手")
        header.setFixedHeight(44)
        header.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #333; "
            "border-bottom: 1px solid #E0E0E0; padding: 12px;"
        )
        layout.addWidget(header)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet("QScrollArea { border: none; background: #F7F7F7; }")

        self._container = QWidget()
        self._container.setStyleSheet("background: #F7F7F7;")
        self._msg_layout = QVBoxLayout(self._container)
        self._msg_layout.setContentsMargins(0, 8, 0, 8)
        self._msg_layout.setSpacing(6)
        self._msg_layout.addStretch()

        self._scroll.setWidget(self._container)
        layout.addWidget(self._scroll, stretch=1)

        input_area = QWidget()
        input_area.setStyleSheet(
            "QWidget { background: #FAFAFA; border-top: 1px solid #E0E0E0; }"
        )
        input_layout = QHBoxLayout(input_area)
        input_layout.setContentsMargins(12, 8, 12, 8)
        input_layout.setSpacing(8)

        self._input = TextEdit()
        self._input.setPlaceholderText("描述你想修改的内容…")
        self._input.setMinimumHeight(42)
        self._input.installEventFilter(self)
        input_layout.addWidget(self._input, stretch=1)

        self._send_btn = PrimaryPushButton("发送")
        self._send_btn.setMinimumHeight(42)
        self._send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._send_btn.clicked.connect(self._on_send)
        input_layout.addWidget(self._send_btn)

        layout.addWidget(input_area)

    def set_current_content(self, content: str) -> None:
        """设置当前大纲内容，供 AI 优化时参考。"""
        self._current_content = content

    def clear_messages(self) -> None:
        """清空消息。"""
        while self._msg_layout.count() > 1:
            item = self._msg_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()

    def _add_bubble(self, role: str, text: str) -> None:
        bubble = _ChatBubble(role, text)
        count = self._msg_layout.count()
        self._msg_layout.insertWidget(count - 1, bubble)
        self._scroll.verticalScrollBar().setValue(
            self._scroll.verticalScrollBar().maximum()
        )

    def _on_send(self) -> None:
        text = self._input.toPlainText().strip()
        if not text or not self._current_content:
            return

        self._add_bubble("user", text)
        self._input.clear()

        self._add_bubble("assistant", "正在思考中…")
        loading_bubble = self._msg_layout.itemAt(self._msg_layout.count() - 2).widget()

        self._send_btn.setEnabled(False)

        self._worker = OptimizeWorker(
            self._text_service, self._current_content, text, "qwen-max"
        )

        def on_finished(result: str) -> None:
            self._send_btn.setEnabled(True)
            if loading_bubble and loading_bubble.parent():
                loading_bubble.setParent(None)
                loading_bubble.deleteLater()
            self._add_bubble("assistant", "已根据你的要求优化大纲，内容已更新到编辑器。")
            self._current_content = result
            self.content_updated.emit(result)

        def on_failed(error: str) -> None:
            self._send_btn.setEnabled(True)
            if loading_bubble and loading_bubble.parent():
                loading_bubble.setParent(None)
                loading_bubble.deleteLater()
            self._add_bubble("assistant", f"优化失败：{error}")

        self._worker.finished.connect(on_finished)
        self._worker.failed.connect(on_failed)
        self._worker.start()

    def eventFilter(self, obj, event) -> bool:
        if obj is self._input and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Return and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self._on_send()
                return True
        return super().eventFilter(obj, event)

class StoryOutlineEditor(QWidget):
    """故事大纲编辑器页面。"""

    back_clicked = pyqtSignal()
    next_step_clicked = pyqtSignal(str)

    def __init__(
        self,
        story_outline_service: StoryOutlineService,
        text_service: TextModelService,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._service = story_outline_service
        self._text_service = text_service
        self._current_outline: StoryOutline | None = None
        self._current_project_id: int | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        toolbar = QWidget()
        toolbar.setStyleSheet("background: white; border-bottom: 1px solid #E0E0E0;")
        toolbar.setFixedHeight(60)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(20, 12, 20, 12)
        toolbar_layout.setSpacing(12)

        back_btn = ToolButton(FluentIcon.LEFT_ARROW)
        back_btn.setFixedSize(36, 36)
        back_btn.setIconSize(QSize(18, 18))
        back_btn.setToolTip("返回项目详情")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.back_clicked.emit)
        toolbar_layout.addWidget(back_btn)

        title_label = QLabel("大纲编辑")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        toolbar_layout.addWidget(title_label, stretch=1)

        self.history_btn = ToolButton(FluentIcon.HISTORY)
        self.history_btn.setFixedSize(36, 36)
        self.history_btn.setIconSize(QSize(18, 18))
        self.history_btn.setToolTip("历史版本")
        self.history_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.history_btn.clicked.connect(self._on_show_history)
        toolbar_layout.addWidget(self.history_btn)

        self.save_btn = PushButton("保存")
        style_button(self.save_btn, "save")
        self.save_btn.clicked.connect(self._on_save)
        toolbar_layout.addWidget(self.save_btn)

        self.next_btn = PushButton("生成剧本")
        self.next_btn.setIcon(FluentIcon.RIGHT_ARROW)
        style_button(self.next_btn, "generate")
        self.next_btn.clicked.connect(self._on_next_step)
        toolbar_layout.addWidget(self.next_btn)

        layout.addWidget(toolbar)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        editor_widget = QWidget()
        editor_layout = QVBoxLayout(editor_widget)
        editor_layout.setContentsMargins(20, 20, 20, 20)
        editor_layout.setSpacing(12)

        editor_title = QLabel("大纲内容")
        editor_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
        editor_layout.addWidget(editor_title)

        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("请输入项目大纲...")
        self.text_edit.setStyleSheet(
            """
            QTextEdit {
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                line-height: 1.6;
                background: white;
            }
            QTextEdit:focus {
                border: 1px solid #0078D4;
            }
            """
        )
        editor_layout.addWidget(self.text_edit, stretch=1)

        self._chat_panel = StoryOutlineChatPanel(self._text_service)
        self._chat_panel.setMinimumWidth(300)
        self._chat_panel.content_updated.connect(self._on_chat_content_updated)

        splitter.addWidget(editor_widget)
        splitter.addWidget(self._chat_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        splitter.setSizes([700, 360])

        layout.addWidget(splitter, stretch=1)

    def load_story_outline(self, project_id: int) -> None:
        """加载项目故事大纲。"""
        self._current_project_id = project_id
        self._current_outline = self._service.get_or_create_story_outline(project_id)

        self.text_edit.setPlainText(self._current_outline.content)
        self._chat_panel.set_current_content(self._current_outline.content)
        self._chat_panel.clear_messages()

    def _on_chat_content_updated(self, new_content: str) -> None:
        """AI 对话返回优化后的内容时，更新编辑器。"""
        self.text_edit.setPlainText(new_content)
        if self._current_outline:
            self._current_outline.content = new_content

    def _on_show_history(self) -> None:
        """弹出历史版本对话框。"""
        if not self._current_outline:
            return

        dialog = HistoryDialog(self._current_outline.id, self._service, self)
        dialog.restore_requested.connect(self._on_restore)
        dialog.exec()

    def _on_save(self) -> None:
        """保存大纲。"""
        if not self._current_outline:
            return

        content = self.text_edit.toPlainText().strip()

        if content == self._current_outline.content:
            QMessageBox.information(self, "提示", "内容未发生变化")
            return

        try:
            self._service.update_story_outline(self._current_outline.id, content)
            self._current_outline.content = content
            self._current_outline.updated_at = get_current_timestamp_ms()
            self._chat_panel.set_current_content(content)

            QMessageBox.information(self, "成功", "大纲已保存")
            logger.info(f"保存大纲：{self._current_outline.id}")

        except Exception as e:
            logger.exception("保存大纲失败")
            QMessageBox.critical(self, "错误", f"保存失败：{e}")

    def _on_restore(self, history_id: int) -> None:
        """恢复历史版本。"""
        if not self._current_outline:
            return

        reply = QMessageBox.question(
            self,
            "确认恢复",
            "确定要恢复到此历史版本吗？当前内容将被保存为新的历史版本。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            self._service.restore_from_history(self._current_outline.id, history_id)

            if self._current_project_id:
                self.load_story_outline(self._current_project_id)

            QMessageBox.information(self, "成功", "已恢复到历史版本")
            logger.info(f"恢复大纲历史版本：{history_id}")

        except Exception as e:
            logger.exception("恢复历史版本失败")
            QMessageBox.critical(self, "错误", f"恢复失败：{e}")

    def _on_next_step(self) -> None:
        """生成剧本。"""
        if not self._current_outline:
            return

        current_content = self.text_edit.toPlainText().strip()
        if current_content != self._current_outline.content:
            reply = QMessageBox.question(
                self,
                "提示",
                "检测到大纲内容有变化，是否先保存大纲再继续？",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
                | QMessageBox.StandardButton.Cancel,
            )

            if reply == QMessageBox.StandardButton.Cancel:
                return
            elif reply == QMessageBox.StandardButton.Yes:
                try:
                    self._service.update_story_outline(self._current_outline.id, current_content)
                    self._current_outline.content = current_content
                    self._current_outline.updated_at = get_current_timestamp_ms()
                    logger.info(f"保存大纲：{self._current_outline.id}")
                except Exception as e:
                    logger.exception("保存大纲失败")
                    QMessageBox.critical(self, "错误", f"保存失败：{e}")
                    return

        self.next_step_clicked.emit(current_content)
