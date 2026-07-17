"""自定义 UI 组件：消息气泡、视频卡片、状态标签。"""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
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


class MessageBubble(QWidget):
    """聊天消息气泡，根据 role 区分左右对齐和颜色。"""

    def __init__(self, role: str, content: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.role = role
        self._setup_ui(content)

    def _setup_ui(self, content: str) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 4, 16, 4)

        is_user = self.role == "user"

        if is_user:
            layout.addSpacerItem(
                QSpacerItem(80, 0, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Minimum)
            )

        bubble = QFrame()
        bg = COLOR_BUBBLE_USER if is_user else COLOR_BUBBLE_AI
        text_color = COLOR_TEXT_USER if is_user else COLOR_TEXT_AI
        bubble.setStyleSheet(
            f"QFrame {{ background-color: {bg}; border-radius: 12px; padding: 10px 14px; }}"
        )
        bubble.setMaximumWidth(560)

        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(12, 8, 12, 8)
        bubble_layout.setSpacing(4)

        label = QLabel(content)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        label.setStyleSheet(f"color: {text_color}; background: transparent; font-size: 14px;")
        bubble_layout.addWidget(label)

        layout.addWidget(bubble)

        if not is_user:
            layout.addSpacerItem(
                QSpacerItem(80, 0, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Minimum)
            )


class VideoStatusCard(QWidget):
    """AI 回复中的视频状态卡片，展示生成进度和视频播放器。"""

    open_folder_clicked = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._local_path = ""
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setStyleSheet(
            "VideoStatusCard { background-color: #F8F8F8; border-radius: 8px; }"
        )
        self.setMaximumWidth(400)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

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

        # 视频预览占位
        self.preview_label = QLabel()
        self.preview_label.setFixedSize(360, 200)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet(
            "background-color: #E8E8E8; border-radius: 6px; color: #999;"
        )
        self.preview_label.hide()
        layout.addWidget(self.preview_label)

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

    def set_generating(self) -> None:
        self.status_label.setText("⏳ 生成中…")
        self.progress_bar.hide()

    def set_downloading(self, progress: int = 0) -> None:
        self.status_label.setText("⬇️ 下载中…")
        self.progress_bar.show()
        self.progress_bar.setValue(progress)

    def set_completed(self, local_path: str) -> None:
        self._local_path = local_path
        self.status_label.setText(f"✅ 已完成")
        self.status_label.setStyleSheet(
            f"color: {COLOR_SUCCESS}; font-size: 13px; background: transparent;"
        )
        self.progress_bar.hide()
        self.preview_label.show()
        self.preview_label.setText("🎬 视频已就绪")
        self.play_btn.show()
        self.folder_btn.show()

    def set_failed(self, error: str) -> None:
        self.status_label.setText(f"❌ 失败: {error}")
        self.status_label.setStyleSheet("color: #E74C3C; font-size: 13px; background: transparent;")
        self.progress_bar.hide()
