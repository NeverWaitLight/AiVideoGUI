"""自定义 UI 组件：消息气泡、视频卡片、状态标签。"""

from __future__ import annotations

import os

from PyQt6.QtCore import QRectF, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QStackedLayout,
    QVBoxLayout,
    QWidget,
)

from ui.styles import (
    COLOR_BUBBLE_AI,
    COLOR_BUBBLE_USER,
    COLOR_SUCCESS,
    COLOR_TEXT_AI,
    COLOR_TEXT_SECONDARY,
    COLOR_TEXT_USER,
)

_ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
_PLACEHOLDER_PATH = os.path.join(_ASSETS_DIR, "video_placeholder.png")


class SpinnerOverlay(QWidget):
    """在父组件上居中绘制旋转弧线加载动画。"""

    def __init__(self, parent: QWidget | None = None, size: int = 36):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._size = size
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(40)

    def _tick(self) -> None:
        self._angle = (self._angle + 30) % 360
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx = self.width() / 2
        cy = self.height() / 2
        r = self._size / 2

        rect = QRectF(cx - r, cy - r, self._size, self._size)

        bg_pen = QPen(QColor(220, 220, 220, 120))
        bg_pen.setWidth(3)
        painter.setPen(bg_pen)
        painter.drawArc(rect, 0, 360 * 16)

        fg_pen = QPen(QColor("#4A90D9"))
        fg_pen.setWidth(3)
        fg_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(fg_pen)
        start = self._angle * 16
        painter.drawArc(rect, start, 90 * 16)

    def start(self) -> None:
        if not self._timer.isActive():
            self._timer.start(40)
        self.show()

    def stop(self) -> None:
        self._timer.stop()
        self.hide()


class MessageBubble(QWidget):
    """聊天消息气泡，根据 role 区分左右对齐和颜色，底部显示时间戳。"""

    def __init__(
        self,
        role: str,
        content: str,
        timestamp: str = "",
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.role = role
        self._setup_ui(content, timestamp)

    def _setup_ui(self, content: str, timestamp: str) -> None:
        outer = QHBoxLayout(self)
        outer.setContentsMargins(16, 2, 16, 2)

        is_user = self.role == "user"

        if is_user:
            outer.addSpacerItem(
                QSpacerItem(80, 0, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Minimum)
            )

        column = QVBoxLayout()
        column.setSpacing(2)
        column.setAlignment(
            Qt.AlignmentFlag.AlignRight if is_user else Qt.AlignmentFlag.AlignLeft
        )

        bubble = QFrame()
        bg = COLOR_BUBBLE_USER if is_user else COLOR_BUBBLE_AI
        text_color = COLOR_TEXT_USER if is_user else COLOR_TEXT_AI
        bubble.setStyleSheet(
            f"QFrame {{ background-color: {bg}; border-radius: 12px; }}"
        )
        bubble.setMaximumWidth(560)

        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(10, 8, 10, 8)
        bubble_layout.setSpacing(4)

        label = QLabel(content)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        label.setStyleSheet(f"color: {text_color}; background: transparent; font-size: 14px;")
        bubble_layout.addWidget(label)

        column.addWidget(bubble)

        if timestamp:
            time_label = QLabel(timestamp)
            time_label.setStyleSheet(
                f"color: {COLOR_TEXT_SECONDARY}; font-size: 11px; background: transparent; "
                f"padding: 0 4px;"
            )
            column.addWidget(time_label)

        outer.addLayout(column)

        if not is_user:
            outer.addSpacerItem(
                QSpacerItem(80, 0, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Minimum)
            )


class VideoStatusCard(QWidget):
    """AI 回复中的视频状态卡片，将回复文字、状态、预览整合在一个气泡内。"""

    open_folder_clicked = pyqtSignal(str)

    PREVIEW_W = 360
    PREVIEW_H = 200

    def __init__(
        self,
        message_text: str = "",
        timestamp: str = "",
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._local_path = ""
        self._setup_ui(message_text, timestamp)

    def _setup_ui(self, message_text: str, timestamp: str) -> None:
        outer = QHBoxLayout(self)
        outer.setContentsMargins(16, 2, 16, 2)

        column = QVBoxLayout()
        column.setSpacing(2)
        column.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # ── 气泡主体 ──
        bubble = QFrame()
        bubble.setStyleSheet(
            f"QFrame {{ background-color: {COLOR_BUBBLE_AI}; border-radius: 12px; }}"
        )
        bubble.setMaximumWidth(420)

        layout = QVBoxLayout(bubble)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)

        # 回复文字
        if message_text:
            self._message_label = QLabel(message_text)
            self._message_label.setWordWrap(True)
            self._message_label.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )
            self._message_label.setStyleSheet(
                f"color: {COLOR_TEXT_AI}; background: transparent; font-size: 14px;"
            )
            layout.addWidget(self._message_label)

        # 状态标签
        self.status_label = QLabel("⏳ 生成中…")
        self.status_label.setStyleSheet(
            f"color: {COLOR_TEXT_SECONDARY}; font-size: 13px; background: transparent;"
        )
        layout.addWidget(self.status_label)

        # 进度条（初始隐藏）
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet(
            """
            QProgressBar {
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #4A90D9;
                border-radius: 3px;
            }
            """
        )
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # 视频预览区：使用 StackedLayout 叠加占位图和完成提示
        self._preview_container = QWidget()
        self._preview_container.setFixedSize(self.PREVIEW_W, self.PREVIEW_H)
        self._preview_container.setStyleSheet("background: transparent;")

        preview_stack = QStackedLayout(self._preview_container)
        preview_stack.setContentsMargins(0, 0, 0, 0)

        # Page 0: 占位预览图 + 转圈动画
        self._generating_page = QWidget()
        self._generating_page.setStyleSheet("background: transparent;")
        gen_layout = QVBoxLayout(self._generating_page)
        gen_layout.setContentsMargins(0, 0, 0, 0)

        self.preview_label = QLabel()
        self.preview_label.setFixedSize(self.PREVIEW_W, self.PREVIEW_H)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("border-radius: 6px;")
        self._load_placeholder_pixmap()
        gen_layout.addWidget(self.preview_label)

        self._spinner = SpinnerOverlay(self._generating_page, size=40)
        self._spinner.move(
            (self.PREVIEW_W - 40) // 2,
            (self.PREVIEW_H - 40) // 2,
        )
        self._spinner.start()

        preview_stack.addWidget(self._generating_page)

        # Page 1: 完成提示
        self._completed_page = QLabel("🎬 视频已就绪")
        self._completed_page.setFixedSize(self.PREVIEW_W, self.PREVIEW_H)
        self._completed_page.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._completed_page.setStyleSheet(
            "background-color: #E8E8E8; border-radius: 6px; color: #999; font-size: 16px;"
        )
        preview_stack.addWidget(self._completed_page)

        self._preview_stack = preview_stack
        self._preview_container.hide()
        layout.addWidget(self._preview_container)

        # 播放按钮
        self.play_btn = QPushButton("▶  播放视频")
        self.play_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #4A90D9; color: white; border: none;
                border-radius: 6px; padding: 8px; font-size: 13px;
            }
            QPushButton:hover { background-color: #357ABD; }
            """
        )
        self.play_btn.hide()
        layout.addWidget(self.play_btn)

        # 打开文件夹按钮
        self.folder_btn = QPushButton("📂  打开文件夹")
        self.folder_btn.setStyleSheet(
            """
            QPushButton {
                background-color: transparent; color: #4A90D9;
                border: 1px solid #4A90D9; border-radius: 6px;
                padding: 6px; font-size: 12px;
            }
            QPushButton:hover { background-color: #E3EDF7; }
            """
        )
        self.folder_btn.hide()
        self.folder_btn.clicked.connect(lambda: self.open_folder_clicked.emit(self._local_path))
        layout.addWidget(self.folder_btn)

        column.addWidget(bubble)

        # 时间戳
        if timestamp:
            time_label = QLabel(timestamp)
            time_label.setStyleSheet(
                f"color: {COLOR_TEXT_SECONDARY}; font-size: 11px; background: transparent; "
                f"padding: 0 4px;"
            )
            column.addWidget(time_label)

        outer.addLayout(column)
        outer.addSpacerItem(
            QSpacerItem(80, 0, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Minimum)
        )

    def _load_placeholder_pixmap(self) -> None:
        if os.path.exists(_PLACEHOLDER_PATH):
            pm = QPixmap(_PLACEHOLDER_PATH).scaled(
                self.PREVIEW_W,
                self.PREVIEW_H,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.preview_label.setPixmap(pm)
        else:
            self.preview_label.setStyleSheet(
                "background-color: #E8E8E8; border-radius: 6px; color: #999;"
            )
            self.preview_label.setText("视频预览")

    def set_generating(self) -> None:
        self.status_label.setText("⏳ 生成中…")
        self.status_label.setStyleSheet(
            f"color: {COLOR_TEXT_SECONDARY}; font-size: 13px; background: transparent;"
        )
        self.progress_bar.hide()
        self._preview_container.show()
        self._preview_stack.setCurrentIndex(0)
        self._spinner.start()

    def set_downloading(self, progress: int = 0) -> None:
        self.status_label.setText("⬇️ 下载中…")
        self.status_label.setStyleSheet(
            f"color: {COLOR_TEXT_SECONDARY}; font-size: 13px; background: transparent;"
        )
        self.progress_bar.show()
        self.progress_bar.setValue(progress)
        self._preview_container.show()
        self._preview_stack.setCurrentIndex(0)
        self._spinner.start()

    def set_completed(self, local_path: str) -> None:
        self._local_path = local_path
        self.status_label.setText("✅ 已完成")
        self.status_label.setStyleSheet(
            f"color: {COLOR_SUCCESS}; font-size: 13px; background: transparent;"
        )
        self.progress_bar.hide()
        self._preview_container.show()
        self._preview_stack.setCurrentIndex(1)
        self._spinner.stop()
        self.play_btn.show()
        self.folder_btn.show()

    def set_failed(self, error: str) -> None:
        self.status_label.setText(f"❌ 失败: {error}")
        self.status_label.setStyleSheet("color: #E74C3C; font-size: 13px; background: transparent;")
        self.progress_bar.hide()
        self._preview_container.show()
        self._preview_stack.setCurrentIndex(0)
        self._spinner.stop()
