"""右侧聊天主区域：标题栏、消息流、输入框。"""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ui.styles import CHAT_AREA_STYLE
from ui.widgets import MessageBubble, VideoStatusCard


class ChatArea(QWidget):
    """右侧聊天主区域组件。"""

    message_sent = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("chatArea")
        self.setStyleSheet(CHAT_AREA_STYLE)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── 顶部标题栏 ──
        header = QWidget()
        header.setObjectName("chatHeader")
        header.setFixedHeight(52)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(20, 10, 20, 10)
        header_layout.setSpacing(2)

        self.title_label = QLabel("AI 视频生成")
        self.title_label.setObjectName("headerTitle")
        header_layout.addWidget(self.title_label)

        self.model_label = QLabel("未选择模型")
        self.model_label.setObjectName("headerModel")
        header_layout.addWidget(self.model_label)

        layout.addWidget(header)

        # ── 消息流滚动区域 ──
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("messageScroll")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.message_container = QWidget()
        self.message_container.setObjectName("messageContainer")
        self.message_layout = QVBoxLayout(self.message_container)
        self.message_layout.setContentsMargins(0, 12, 0, 12)
        self.message_layout.setSpacing(8)
        self.message_layout.addStretch()

        self.scroll_area.setWidget(self.message_container)
        layout.addWidget(self.scroll_area, stretch=1)

        # ── 底部输入区 ──
        input_area = QWidget()
        input_area.setObjectName("inputArea")
        input_area.setFixedHeight(80)
        input_layout = QHBoxLayout(input_area)
        input_layout.setContentsMargins(16, 16, 16, 16)
        input_layout.setSpacing(10)

        self.input_box = QTextEdit()
        self.input_box.setObjectName("inputBox")
        self.input_box.setPlaceholderText("输入视频描述…（Enter 发送，Shift+Enter 换行）")
        self.input_box.setFixedHeight(48)
        self.input_box.installEventFilter(self)
        input_layout.addWidget(self.input_box, stretch=1)

        self.send_btn = QPushButton("发送")
        self.send_btn.setObjectName("sendBtn")
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.clicked.connect(self._on_send)
        input_layout.addWidget(self.send_btn)

        layout.addWidget(input_area)

        self._show_welcome()

    def _show_welcome(self) -> None:
        welcome = QLabel("👋  你好！输入文字描述，AI 将为你生成视频。")
        welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome.setStyleSheet("color: #AAAAAA; font-size: 14px; padding: 60px 20px;")
        self.message_layout.insertWidget(0, welcome)
        self._welcome_label = welcome

    def _on_send(self) -> None:
        text = self.input_box.toPlainText().strip()
        if not text:
            return
        self.input_box.clear()
        self.message_sent.emit(text)

    def eventFilter(self, obj, event) -> bool:
        if obj is self.input_box and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Return and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self._on_send()
                return True
        return super().eventFilter(obj, event)

    def add_user_message(self, text: str) -> None:
        if hasattr(self, "_welcome_label") and self._welcome_label:
            self._welcome_label.hide()
            self._welcome_label = None

        bubble = MessageBubble("user", text)
        count = self.message_layout.count()
        self.message_layout.insertWidget(count - 1, bubble)
        self._scroll_to_bottom()

    def add_ai_message(self, text: str) -> MessageBubble:
        bubble = MessageBubble("assistant", text)
        count = self.message_layout.count()
        self.message_layout.insertWidget(count - 1, bubble)
        self._scroll_to_bottom()
        return bubble

    def add_video_card(self) -> VideoStatusCard:
        card = VideoStatusCard()
        count = self.message_layout.count()
        wrapper = QWidget()
        wrapper.setStyleSheet("background: transparent;")
        wrapper_layout = QHBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(16, 0, 16, 0)
        wrapper_layout.addWidget(card)
        wrapper_layout.addStretch()
        self.message_layout.insertWidget(count - 1, wrapper)
        self._scroll_to_bottom()
        return card

    def set_header(self, title: str, model: str) -> None:
        self.title_label.setText(title)
        self.model_label.setText(model)

    def _scroll_to_bottom(self) -> None:
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
