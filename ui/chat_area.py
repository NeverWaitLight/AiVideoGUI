"""右侧聊天主区域：标题栏、消息流、参数面板、输入框。"""

from __future__ import annotations

from typing import Any

from PyQt6.QtCore import QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ui.styles import CHAT_AREA_STYLE, COLOR_PRIMARY
from ui.widgets import MessageBubble, VideoStatusCard


class ToggleSwitch(QWidget):
    """iOS 风格滑动开关组件。"""

    toggled = pyqtSignal(bool)

    def __init__(self, checked: bool = False, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedSize(40, 22)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._checked = checked
        self._anim_pos = 1.0 if checked else 0.0

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, checked: bool) -> None:
        if checked == self._checked:
            return
        self._checked = checked
        self._anim_pos = 1.0 if checked else 0.0
        self.update()
        self.toggled.emit(checked)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.setChecked(not self._checked)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        r = h / 2

        if self._checked:
            bg = QColor(COLOR_PRIMARY)
        else:
            bg = QColor("#CCCCCC")

        painter.setBrush(bg)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(QRectF(0, 0, w, h), r, r)

        knob_r = h - 4
        margin = 2
        if self._checked:
            knob_x = w - knob_r - margin
        else:
            knob_x = margin

        painter.setBrush(QColor("#FFFFFF"))
        painter.drawEllipse(QRectF(knob_x, margin, knob_r, knob_r))


class ParameterPanel(QFrame):
    """视频生成参数选择面板，位于输入框上方。"""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("paramPanel")
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setStyleSheet(
            """
            QFrame#paramPanel {
                background-color: #FAFAFA;
                border-top: 1px solid #E0E0E0;
            }
            QLabel#paramLabel {
                font-size: 12px;
                color: #666666;
            }
            QComboBox#paramCombo {
                border: 1px solid #D0D0D0;
                border-radius: 4px;
                padding: 3px 8px;
                font-size: 12px;
                background: white;
                min-height: 22px;
            }
            QComboBox#paramCombo:focus { border-color: """
            + COLOR_PRIMARY
            + """; }
            """
        )

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 6, 16, 6)
        outer.setSpacing(0)

        # ── 参数控件行 ──
        params_widget = QWidget()
        params_widget.setStyleSheet("background: transparent;")
        params_layout = QHBoxLayout(params_widget)
        params_layout.setContentsMargins(0, 0, 0, 0)
        params_layout.setSpacing(10)

        # 分辨率
        self._resolution_combo = self._make_combo(["480P", "720P", "1080P"], default="720P")
        params_layout.addWidget(
            self._make_param_group("分辨率", self._resolution_combo), stretch=1
        )

        # 时长
        self._duration_combo = self._make_combo(["5秒", "10秒", "15秒"])
        params_layout.addWidget(
            self._make_param_group("时长", self._duration_combo), stretch=1
        )

        # 画面比例
        self._ratio_combo = self._make_combo(["16:9", "9:16", "1:1"])
        params_layout.addWidget(
            self._make_param_group("比例", self._ratio_combo), stretch=1
        )

        # 自动优化
        self._prompt_extend_switch = ToggleSwitch(checked=True)
        params_layout.addWidget(
            self._make_param_group("自动优化", self._prompt_extend_switch), stretch=1
        )

        # 水印
        self._watermark_switch = ToggleSwitch(checked=False)
        params_layout.addWidget(
            self._make_param_group("水印", self._watermark_switch), stretch=1
        )

        outer.addWidget(params_widget)

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
    def _make_combo(items: list[str], default: str = "") -> QComboBox:
        combo = QComboBox()
        combo.setObjectName("paramCombo")
        combo.addItems(items)
        if default:
            combo.setCurrentText(default)
        return combo

    def get_params(self) -> dict[str, Any]:
        """返回当前选中的生成参数，字段名与 DashScope API 一一对应。"""
        duration_map = {"5秒": 5, "10秒": 10, "15秒": 15}
        return {
            "resolution": self._resolution_combo.currentText(),
            "ratio": self._ratio_combo.currentText(),
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

        # ── 参数面板 ──
        self.param_panel = ParameterPanel()
        layout.addWidget(self.param_panel)

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
