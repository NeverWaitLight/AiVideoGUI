"""项目管理页面：网格布局展示项目卡片。"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QPainter, QColor
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
    QFormLayout,
    QComboBox,
    QGridLayout,
    QScrollArea,
    QFileDialog,
)
from qfluentwidgets import (
    PrimaryPushButton,
    PushButton,
    ToolButton,
    FluentIcon,
    LineEdit,
    CardWidget,
)

from models.data_models import Project
from service.project_service import ProjectService

logger = logging.getLogger(__name__)


def _format_time(dt: datetime) -> str:
    """将 datetime 格式化为显示时间。"""
    now = datetime.now()
    if dt.date() == now.date():
        return dt.strftime("%H:%M")
    return dt.strftime("%m-%d %H:%M")


# 分辨率映射表
RESOLUTION_MAP = {
    "16:9": {
        "480P": "854x480",
        "720P": "1280x720",
        "1080P": "1920x1080",
        "2K": "2560x1440",
        "4K": "3840x2160",
    },
    "9:16": {
        "480P": "480x854",
        "720P": "720x1280",
        "1080P": "1080x1920",
        "2K": "1440x2560",
        "4K": "2160x3840",
    },
    "4:3": {
        "480P": "640x480",
        "720P": "960x720",
        "1080P": "1440x1080",
        "2K": "1920x1440",
        "4K": "2880x2160",
    },
    "3:4": {
        "480P": "480x640",
        "720P": "720x960",
        "1080P": "1080x1440",
        "2K": "1440x1920",
        "4K": "2160x2880",
    },
}


class ProjectCard(CardWidget):
    """项目卡片控件。"""

    project_clicked = pyqtSignal(str)  # project_id，重命名避免与父类 clicked 信号冲突
    edit_clicked = pyqtSignal(str)
    delete_clicked = pyqtSignal(str)

    def __init__(self, project: Project, parent: QWidget | None = None):
        super().__init__(parent)
        self._project = project
        self.setFixedSize(220, 280)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 封面图区域（160x160）
        cover_container = QWidget()
        cover_container.setFixedSize(220, 160)
        cover_container.setStyleSheet("background: #F5F5F5;")
        cover_layout = QVBoxLayout(cover_container)
        cover_layout.setContentsMargins(0, 0, 0, 0)

        self._cover_label = QLabel()
        self._cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._cover_label.setScaledContents(False)
        self._load_cover_image()
        cover_layout.addWidget(self._cover_label)

        layout.addWidget(cover_container)

        # 信息区域
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(12, 10, 12, 10)
        info_layout.setSpacing(6)

        # 项目名称
        name_label = QLabel(self._project.name)
        name_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
        name_label.setWordWrap(True)
        name_label.setMaximumHeight(40)
        info_layout.addWidget(name_label)

        # 项目信息
        info_text = f"{self._project.aspect_ratio} · {self._get_resolution_name()}"
        info_label = QLabel(info_text)
        info_label.setStyleSheet("font-size: 12px; color: #666;")
        info_layout.addWidget(info_label)

        # 创建时间
        time_label = QLabel(_format_time(self._project.created_at))
        time_label.setStyleSheet("font-size: 11px; color: #999;")
        info_layout.addWidget(time_label)

        info_layout.addStretch()

        # 操作按钮行
        btn_row = QWidget()
        btn_layout = QHBoxLayout(btn_row)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(6)
        btn_layout.addStretch()

        edit_btn = ToolButton(FluentIcon.EDIT)
        edit_btn.setFixedSize(28, 28)
        edit_btn.setIconSize(QSize(16, 16))
        edit_btn.setToolTip("编辑项目")
        edit_btn.clicked.connect(lambda: self.edit_clicked.emit(self._project.id))
        btn_layout.addWidget(edit_btn)

        delete_btn = ToolButton(FluentIcon.DELETE)
        delete_btn.setFixedSize(28, 28)
        delete_btn.setIconSize(QSize(16, 16))
        delete_btn.setToolTip("删除项目")
        delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self._project.id))
        btn_layout.addWidget(delete_btn)

        info_layout.addWidget(btn_row)

        layout.addWidget(info_widget)

    def _load_cover_image(self) -> None:
        """加载封面图，如果没有则显示默认图标。"""
        if self._project.cover_image and os.path.exists(self._project.cover_image):
            pixmap = QPixmap(self._project.cover_image)
            if not pixmap.isNull():
                # 等比缩放到 220x160
                scaled = pixmap.scaled(
                    220, 160,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation
                )
                self._cover_label.setPixmap(scaled)
                return

        # 加载默认图标
        default_icon_path = Path(__file__).parent / "assets" / "default_project_cover.svg"
        if default_icon_path.exists():
            pixmap = QPixmap(str(default_icon_path))
            if not pixmap.isNull():
                # 按宽度对齐缩放，高度自适应
                scaled = pixmap.scaled(
                    220, 160,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self._cover_label.setPixmap(scaled)
        else:
            # 如果默认图标也不存在，显示占位符
            self._cover_label.setText("📁")
            self._cover_label.setStyleSheet("font-size: 64px;")

    def _get_resolution_name(self) -> str:
        """根据分辨率获取显示名称（如 720P）。"""
        for res_name, res_value in RESOLUTION_MAP.get(self._project.aspect_ratio, {}).items():
            if res_value == self._project.resolution:
                return res_name
        return self._project.resolution

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.project_clicked.emit(self._project.id)
        super().mousePressEvent(event)


class ProjectDialog(QDialog):
    """创建/编辑项目对话框。"""

    def __init__(self, parent: QWidget | None = None, project: Project | None = None):
        super().__init__(parent)
        self._project = project
        self._cover_image_path = project.cover_image if project else ""
        self.setWindowTitle("编辑项目" if project else "新建项目")
        self.setFixedSize(450, 400)
        self._setup_ui()

        if project:
            self._load_project_data()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # 表单
        form = QFormLayout()
        form.setSpacing(12)

        self._name_input = LineEdit()
        self._name_input.setPlaceholderText("输入项目名称")
        form.addRow("项目名称", self._name_input)

        # 封面图选择
        cover_widget = QWidget()
        cover_layout = QHBoxLayout(cover_widget)
        cover_layout.setContentsMargins(0, 0, 0, 0)
        cover_layout.setSpacing(8)

        self._cover_path_label = QLabel("未选择")
        self._cover_path_label.setStyleSheet("color: #999; font-size: 12px;")
        cover_layout.addWidget(self._cover_path_label, stretch=1)

        self._choose_cover_btn = PushButton("选择图片")
        self._choose_cover_btn.clicked.connect(self._on_choose_cover)
        cover_layout.addWidget(self._choose_cover_btn)

        self._clear_cover_btn = PushButton("清除")
        self._clear_cover_btn.clicked.connect(self._on_clear_cover)
        cover_layout.addWidget(self._clear_cover_btn)

        form.addRow("封面图", cover_widget)

        # 画面比例
        self._ratio_combo = QComboBox()
        self._ratio_combo.addItems(["16:9", "9:16", "4:3", "3:4"])
        self._ratio_combo.currentTextChanged.connect(self._on_ratio_changed)
        form.addRow("画面比例", self._ratio_combo)

        # 分辨率
        self._resolution_combo = QComboBox()
        form.addRow("分辨率", self._resolution_combo)

        layout.addLayout(form)
        layout.addStretch()

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = PushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        self._ok_btn = PrimaryPushButton("确定")
        self._ok_btn.clicked.connect(self._on_ok)
        btn_layout.addWidget(self._ok_btn)

        layout.addLayout(btn_layout)

        # 初始化分辨率选项
        self._on_ratio_changed("16:9")

    def _on_ratio_changed(self, ratio: str) -> None:
        """比例改变时，更新分辨率选项。"""
        self._resolution_combo.clear()
        resolutions = list(RESOLUTION_MAP.get(ratio, {}).keys())
        self._resolution_combo.addItems(resolutions)
        if "720P" in resolutions:
            self._resolution_combo.setCurrentText("720P")

    def _on_choose_cover(self) -> None:
        """选择封面图片。"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择封面图片",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.svg)"
        )
        if file_path:
            self._cover_image_path = file_path
            self._cover_path_label.setText(Path(file_path).name)
            self._cover_path_label.setStyleSheet("color: #333; font-size: 12px;")

    def _on_clear_cover(self) -> None:
        """清除封面图。"""
        self._cover_image_path = ""
        self._cover_path_label.setText("未选择")
        self._cover_path_label.setStyleSheet("color: #999; font-size: 12px;")

    def _load_project_data(self) -> None:
        """加载项目数据到表单。"""
        if not self._project:
            return

        self._name_input.setText(self._project.name)
        self._ratio_combo.setCurrentText(self._project.aspect_ratio)

        # 根据分辨率找到对应的名称
        for res_name, res_value in RESOLUTION_MAP.get(self._project.aspect_ratio, {}).items():
            if res_value == self._project.resolution:
                self._resolution_combo.setCurrentText(res_name)
                break

        # 封面图
        if self._project.cover_image and os.path.exists(self._project.cover_image):
            self._cover_path_label.setText(Path(self._project.cover_image).name)
            self._cover_path_label.setStyleSheet("color: #333; font-size: 12px;")

    def _on_ok(self) -> None:
        name = self._name_input.text().strip()
        if not name:
            return

        self.accept()

    def get_data(self) -> dict:
        """获取表单数据。"""
        ratio = self._ratio_combo.currentText()
        res_name = self._resolution_combo.currentText()
        resolution = RESOLUTION_MAP.get(ratio, {}).get(res_name, "1280x720")

        return {
            "name": self._name_input.text().strip(),
            "resolution": resolution,
            "aspect_ratio": ratio,
            "cover_image": self._cover_image_path,
        }


class ProjectGridPage(QWidget):
    """项目网格视图页面。"""

    project_selected = pyqtSignal(str)  # project_id

    def __init__(self, project_service: ProjectService, parent: QWidget | None = None):
        super().__init__(parent)
        self._service = project_service
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 顶部区域：标题 + 新建按钮
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(12)

        title = QLabel("项目管理")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #333;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        new_btn = PrimaryPushButton(FluentIcon.ADD, "新建项目")
        new_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        new_btn.clicked.connect(self._on_new_project)
        header_layout.addWidget(new_btn)

        layout.addWidget(header)

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        # 网格容器
        self._grid_container = QWidget()
        self._grid_layout = QGridLayout(self._grid_container)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)
        self._grid_layout.setSpacing(20)
        self._grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        scroll.setWidget(self._grid_container)
        layout.addWidget(scroll, stretch=1)

    def load_projects(self) -> None:
        """加载并显示所有项目。"""
        # 清空现有卡片
        while self._grid_layout.count():
            item = self._grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        projects = self._service.list_projects()
        row, col = 0, 0
        max_cols = 4  # 每行最多4个卡片

        for project in projects:
            card = ProjectCard(project)
            card.project_clicked.connect(self.project_selected.emit)
            card.edit_clicked.connect(self._on_edit_project)
            card.delete_clicked.connect(self._on_delete_project)

            self._grid_layout.addWidget(card, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def _on_new_project(self) -> None:
        """新建项目。"""
        dialog = ProjectDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            self._service.create_project(
                name=data["name"],
                resolution=data["resolution"],
                aspect_ratio=data["aspect_ratio"],
                cover_image=data["cover_image"],
            )
            self.load_projects()

    def _on_edit_project(self, project_id: str) -> None:
        """编辑项目。"""
        project = self._service.get_project(project_id)
        if not project:
            return

        dialog = ProjectDialog(self, project)
        if dialog.exec():
            data = dialog.get_data()
            self._service.update_project(
                project_id=project_id,
                name=data["name"],
                resolution=data["resolution"],
                aspect_ratio=data["aspect_ratio"],
                cover_image=data["cover_image"],
            )
            self.load_projects()

    def _on_delete_project(self, project_id: str) -> None:
        """删除项目。"""
        self._service.delete_project(project_id)
        self.load_projects()
