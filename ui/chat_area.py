"""右侧聊天主区域：标题栏、消息流、参数面板、输入框。"""

from __future__ import annotations

from typing import Any

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    TextEdit,
    PrimaryPushButton,
    ComboBox,
    SwitchButton,
)

from ui.widgets import MessageBubble, VideoStatusCard


class ParameterPanel(QFrame):
    """视频生成参数选择面板，位于输入框上方。"""

    # 画面比例到分辨率的映射
    RESOLUTION_MAP = {
        "16:9": ["480P", "720P", "1080P", "2K", "4K"],
        "9:16": ["480P", "720P", "1080P", "2K", "4K"],
        "4:3": ["480P", "720P", "1080P", "2K", "4K"],
        "3:4": ["480P", "720P", "1080P", "2K", "4K"],
    }

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("paramPanel")
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setStyleSheet(
            """
            QLabel#paramLabel {
                font-size: 12px;
                color: #666666;
            }
            """
        )

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 6, 0, 6)
        outer.setSpacing(0)

        # ── 参数控件行 ──
        params_widget = QWidget()
        params_widget.setStyleSheet("background: transparent;")
        params_layout = QHBoxLayout(params_widget)
        params_layout.setContentsMargins(0, 0, 0, 0)
        params_layout.setSpacing(10)

        # 画面比例（第一个）
        self._ratio_combo = self._make_combo(["16:9", "9:16", "4:3", "3:4"])
        params_layout.addWidget(
            self._make_param_group("比例", self._ratio_combo), stretch=1
        )

        # 分辨率（第二个，根据比例动态变化）
        self._resolution_combo = ComboBox()
        params_layout.addWidget(
            self._make_param_group("分辨率", self._resolution_combo), stretch=1
        )

        # 时长
        self._duration_combo = self._make_combo(["5秒", "10秒", "15秒"])
        params_layout.addWidget(
            self._make_param_group("时长", self._duration_combo), stretch=1
        )

        # 自动优化
        self._prompt_extend_switch = SwitchButton()
        self._prompt_extend_switch.setChecked(True)
        params_layout.addWidget(
            self._make_param_group("自动优化", self._prompt_extend_switch), stretch=1
        )

        # 水印
        self._watermark_switch = SwitchButton()
        params_layout.addWidget(
            self._make_param_group("水印", self._watermark_switch), stretch=1
        )

        outer.addWidget(params_widget)

        # 连接信号（在控件创建完成后）
        self._ratio_combo.currentTextChanged.connect(self._on_ratio_changed)

        # 初始化分辨率选项（手动触发一次）
        self._on_ratio_changed("16:9")

    def _on_ratio_changed(self, ratio: str) -> None:
        """比例改变时，更新分辨率选项。"""
        self._resolution_combo.clear()
        resolutions = self.RESOLUTION_MAP.get(ratio, [])
        self._resolution_combo.addItems(resolutions)
        # 默认选择 720P
        if "720P" in resolutions:
            self._resolution_combo.setCurrentText("720P")

    @staticmethod
    def _make_param_group(label_text: str, control: QWidget) -> QWidget:
        group = QWidget()
        group.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(group)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        lbl = QLabel(label_text)
        lbl.setObjectName("paramLabel")
        layout.addWidget(lbl)
        layout.addWidget(control)
        layout.addStretch()
        return group

    @staticmethod
    def _make_combo(items: list[str], default: str = "") -> ComboBox:
        combo = ComboBox()
        combo.addItems(items)
        if default:
            combo.setCurrentText(default)
        return combo

    def get_params(self) -> dict[str, Any]:
        """返回当前选中的生成参数，字段名与 DashScope API 一一对应。"""
        duration_map = {"5秒": 5, "10秒": 10, "15秒": 15}

        ratio = self._ratio_combo.currentText()
        resolution = self._resolution_combo.currentText()

        return {
            "resolution": resolution,
            "ratio": ratio,
            "duration": duration_map.get(self._duration_combo.currentText(), 5),
            "prompt_extend": self._prompt_extend_switch.isChecked(),
            "watermark": self._watermark_switch.isChecked(),
        }


class ChatArea(QWidget):
    """右侧聊天主区域组件。"""

    message_sent = pyqtSignal(str, dict)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("chatArea")
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

        # ── 底部区域：参数面板 + 输入框（统一容器，确保水平对齐） ──
        bottom = QWidget()
        bottom.setObjectName("bottomSection")
        bottom.setStyleSheet(
            """
            QWidget#bottomSection {
                background-color: #FAFAFA;
                border-top: 1px solid #E0E0E0;
            }
            """
        )
        bottom_layout = QVBoxLayout(bottom)
        bottom_layout.setContentsMargins(16, 0, 16, 0)
        bottom_layout.setSpacing(0)

        # 参数面板
        self.param_panel = ParameterPanel()
        bottom_layout.addWidget(self.param_panel)

        # 输入行
        input_row = QWidget()
        input_row.setStyleSheet("background: transparent;")
        input_row.setFixedHeight(70)
        input_layout = QHBoxLayout(input_row)
        input_layout.setContentsMargins(0, 10, 0, 12)
        input_layout.setSpacing(10)

        self.input_box = TextEdit()
        self.input_box.setPlaceholderText("输入视频描述…（Enter 发送，Shift+Enter 换行）")
        self.input_box.setFixedHeight(48)
        self.input_box.installEventFilter(self)
        input_layout.addWidget(self.input_box, stretch=1)

        self.send_btn = PrimaryPushButton("发送")
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.clicked.connect(self._on_send)
        input_layout.addWidget(self.send_btn)

        bottom_layout.addWidget(input_row)
        layout.addWidget(bottom)

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
        params = self.param_panel.get_params()
        self.input_box.clear()
        self.message_sent.emit(text, params)

    def eventFilter(self, obj, event) -> bool:
        if obj is self.input_box and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Return and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self._on_send()
                return True
        return super().eventFilter(obj, event)

    def add_user_message(self, text: str, timestamp: str = "") -> None:
        if hasattr(self, "_welcome_label") and self._welcome_label:
            self._welcome_label.hide()
            self._welcome_label = None

        bubble = MessageBubble("user", text, timestamp)
        count = self.message_layout.count()
        self.message_layout.insertWidget(count - 1, bubble)
        self._scroll_to_bottom()

    def add_ai_message(self, text: str, timestamp: str = "") -> MessageBubble:
        bubble = MessageBubble("assistant", text, timestamp)
        count = self.message_layout.count()
        self.message_layout.insertWidget(count - 1, bubble)
        self._scroll_to_bottom()
        return bubble

    def add_ai_message_with_card(self, text: str, timestamp: str = "") -> VideoStatusCard:
        """添加包含回复文字 + 视频状态卡片的整合气泡。"""
        return self.add_video_card(message_text=text, timestamp=timestamp)

    def add_video_card(
        self, message_text: str = "", timestamp: str = ""
    ) -> VideoStatusCard:
        card = VideoStatusCard(message_text=message_text, timestamp=timestamp)
        count = self.message_layout.count()
        self.message_layout.insertWidget(count - 1, card)
        self._scroll_to_bottom()
        return card

    def clear_messages(self) -> None:
        while self.message_layout.count() > 1:
            item = self.message_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()
        self._show_welcome()

    def set_header(self, title: str, model: str) -> None:
        self.title_label.setText(title)
        self.model_label.setText(model)

    def _scroll_to_bottom(self) -> None:
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
