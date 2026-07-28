"""可复用的页面标题栏组件，统一所有子页面的顶部导航栏布局。"""

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QWidget
from qfluentwidgets import FluentIcon, ToolButton


class PageHeader(QWidget):
    """统一页面标题栏：返回按钮 + 标题 + 可选副标题 + 右侧操作区。"""

    back_clicked = pyqtSignal()

    def __init__(self, title: str = "", show_back: bool = True, parent: QWidget | None = None):
        super().__init__(parent)
        self.setStyleSheet(
            "PageHeader { background: white; border: none; border-bottom: 1px solid #E0E0E0; }"
        )
        self.setFixedHeight(56)

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(20, 0, 20, 0)
        self._layout.setSpacing(12)

        # ── 返回按钮 ──
        self._back_btn = ToolButton(FluentIcon.LEFT_ARROW)
        self._back_btn.setFixedSize(36, 36)
        self._back_btn.setIconSize(QSize(18, 18))
        self._back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._back_btn.clicked.connect(self.back_clicked.emit)
        self._back_btn.setVisible(show_back)
        self._layout.addWidget(self._back_btn)

        # ── 标题 ──
        self._title_label = QLabel(title)
        self._title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        self._layout.addWidget(self._title_label)

        # ── 副标题（默认隐藏） ──
        self._separator_label = QLabel("·")
        self._separator_label.setStyleSheet("font-size: 16px; color: #999;")
        self._separator_label.hide()
        self._layout.addWidget(self._separator_label)

        self._subtitle_label = QLabel("")
        self._subtitle_label.setStyleSheet("font-size: 13px; color: #666;")
        self._subtitle_label.hide()
        self._layout.addWidget(self._subtitle_label)

        self._layout.addStretch()

        # ── 右侧操作区 ──
        self._actions_widget = QWidget()
        self._actions_widget.setStyleSheet("background: transparent;")
        self._actions_layout = QHBoxLayout(self._actions_widget)
        self._actions_layout.setContentsMargins(0, 0, 0, 0)
        self._actions_layout.setSpacing(8)
        self._layout.addWidget(self._actions_widget)

    def set_title(self, text: str) -> None:
        self._title_label.setText(text)

    def title(self) -> str:
        return self._title_label.text()

    def set_subtitle(self, text: str) -> None:
        has_text = bool(text)
        self._separator_label.setVisible(has_text)
        self._subtitle_label.setVisible(has_text)
        if has_text:
            self._subtitle_label.setText(text)

    def set_back_visible(self, visible: bool) -> None:
        self._back_btn.setVisible(visible)

    def set_back_tooltip(self, text: str) -> None:
        self._back_btn.setToolTip(text)

    def add_action(self, widget: QWidget) -> None:
        self._actions_layout.addWidget(widget)


def create_icon_button(
    icon, tooltip: str = "", parent: QWidget | None = None
) -> ToolButton:
    """创建统一规格的图标按钮（36×36，图标 18×18）。"""
    btn = ToolButton(icon, parent)
    btn.setFixedSize(36, 36)
    btn.setIconSize(QSize(18, 18))
    if tooltip:
        btn.setToolTip(tooltip)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    return btn
