"""左侧垂直 Tab 栏：切换直接生成和项目管理模式。"""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QButtonGroup
from qfluentwidgets import ToolButton, FluentIcon


class TabBar(QWidget):
    """垂直 Tab 栏组件。"""

    tab_changed = pyqtSignal(int)  # 0: 直接生成, 1: 项目管理

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("tabBar")
        self.setFixedWidth(60)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 16, 8, 8)
        layout.setSpacing(12)

        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)

        # 直接生成按钮
        self.direct_btn = ToolButton(FluentIcon.CHAT)
        self.direct_btn.setFixedSize(44, 44)
        self.direct_btn.setIconSize(QSize(24, 24))
        self.direct_btn.setCheckable(True)
        self.direct_btn.setChecked(True)
        self.direct_btn.setToolTip("直接生成")
        self.direct_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.button_group.addButton(self.direct_btn, 0)
        layout.addWidget(self.direct_btn)

        # 项目管理按钮
        self.project_btn = ToolButton(FluentIcon.FOLDER)
        self.project_btn.setFixedSize(44, 44)
        self.project_btn.setIconSize(QSize(24, 24))
        self.project_btn.setCheckable(True)
        self.project_btn.setToolTip("项目管理")
        self.project_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.button_group.addButton(self.project_btn, 1)
        layout.addWidget(self.project_btn)

        layout.addStretch()

        # 连接信号
        self.button_group.idClicked.connect(self.tab_changed.emit)

        # 应用样式
        self._apply_styles()

    def _apply_styles(self) -> None:
        """应用按钮选中/未选中样式。"""
        style = """
        QWidget#tabBar {
            background-color: #FAFAFA;
            border-right: 1px solid #E0E0E0;
        }
        ToolButton {
            border: none;
            border-radius: 8px;
            background-color: transparent;
        }
        ToolButton:hover {
            background-color: rgba(0, 0, 0, 0.05);
        }
        ToolButton:checked {
            background-color: #E3F2FD;
        }
        ToolButton:checked:hover {
            background-color: #BBDEFB;
        }
        """
        self.setStyleSheet(style)

    def set_current_tab(self, index: int) -> None:
        """设置当前选中的 Tab（0: 直接生成, 1: 项目管理）。"""
        if index == 0:
            self.direct_btn.setChecked(True)
        elif index == 1:
            self.project_btn.setChecked(True)
