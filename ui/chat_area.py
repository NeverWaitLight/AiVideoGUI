"""右侧聊天主区域：标题栏、消息流、输入框。"""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
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
        header.setFixedHeight(60)
        header.setStyleSheet("border-bottom: 1px solid #E0E0E0;")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(20, 8, 20, 8)
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
        input_area.setFixedHeight(100)
        input_area.setStyleSheet("border-top: 1px solid #E0E0E0;")
        input_layout = QHBoxLayout(input_area)
        input_layout.setContentsMargins(16, 12, 16, 12)
        input_layout.setSpacing(12)

        self.input_box = QTextEdit()
        self.input_box.setObjectName("inputBox")
        self.input_box.setPlaceholderText("输入视频描述…（Enter 发送，Shift+Enter 换行）")
        self.input_box.setMaximumHeight(76)
        self.input_box.installEventFilter(self)
        input_layout.addWidget(self.input_box, stretch=1)

        self.send_btn = QPushButton("发送")
        self.send_btn.setObjectName("sendBtn")
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.setFixedHeight(42)
        self.send_btn.clicked.connect(self._on_send)
        input_layout.addWidget(self.send_btn)

        layout.addWidget(input_area)

        # 欢迎信息
        self._show_welcome()

    def _show_welcome(self) -> None:
        welcome = QLabel("👋 你好！输入文字描述，AI 将为你生成视频。")
        welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome.setStyleSheet("color: #999; font-size: 15px; padding: 40px;")
        self.message_layout.insertWidget(0, welcome)
        self._welcome_label = welcome

    def _on_send(self) -> None:
        text = self.input_box.toPlainText().strip()
        if not text:
            return
        self.input_box.clear()
        self.message_sent.emit(text)

    def eventFilter(self, obj, event) -> bool:
        """拦截输入框的 Enter 键实现发送。"""
        if obj is self.input_box and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Return and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self._on_send()
                return True
        return super().eventFilter(obj, event)

    def add_user_message(self, text: str) -> None:
        """添加一条用户消息气泡。"""
        if hasattr(self, "_welcome_label") and self._welcome_label:
            self._welcome_label.hide()
            self._welcome_label = None

        bubble = MessageBubble("user", text)
        # 插入到 stretch 之前
        count = self.message_layout.count()
        self.message_layout.insertWidget(count - 1, bubble)
        self._scroll_to_bottom()

    def add_ai_message(self, text: str) -> MessageBubble:
        """添加一条 AI 回复气泡。"""
        bubble = MessageBubble("assistant", text)
        count = self.message_layout.count()
        self.message_layout.insertWidget(count - 1, bubble)
        self._scroll_to_bottom()
        return bubble

    def add_video_card(self) -> VideoStatusCard:
        """添加一个视频状态卡片到消息流。"""
        card = VideoStatusCard()
        count = self.message_layout.count()
        # 靠左对齐：卡片前加 stretch
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
