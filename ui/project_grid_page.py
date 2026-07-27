"""项目管理页面：网格布局展示项目卡片。"""

from __future__ import annotations

import logging
import os
import random
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
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
from ui.styles import style_button
from utils.time_format import format_timestamp_short

logger = logging.getLogger(__name__)


def _format_time(timestamp: int) -> str:
    """将时间戳格式化为显示时间。"""
    return format_timestamp_short(timestamp)


class ProjectCard(CardWidget):
    """项目卡片控件。"""

    project_clicked = pyqtSignal(int)  # project_id，重命名避免与父类 clicked 信号冲突
    edit_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)

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
        info_text = f"{self._project.aspect_ratio} · {self._project.resolution}"
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
        resolutions = ["480P", "720P", "1080P", "2K", "4K"]
        self._resolution_combo.addItems(resolutions)
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
        self._resolution_combo.setCurrentText(self._project.resolution)

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
        return {
            "name": self._name_input.text().strip(),
            "resolution": self._resolution_combo.currentText(),
            "aspect_ratio": self._ratio_combo.currentText(),
            "cover_image": self._cover_image_path,
        }


class ProjectGridPage(QWidget):
    """项目网格视图页面。"""

    project_selected = pyqtSignal(int)  # project_id

    def __init__(self, project_service: ProjectService, parent: QWidget | None = None):
        super().__init__(parent)
        self._service = project_service
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 顶部区域：标题 + 新建按钮
        self._header = QWidget()
        header_layout = QHBoxLayout(self._header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(12)

        title = QLabel("项目管理")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #333;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # 右上角的新建按钮
        self._header_new_btn = PrimaryPushButton(FluentIcon.ADD, "新建项目")
        self._header_new_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._header_new_btn.clicked.connect(self._on_new_project)
        header_layout.addWidget(self._header_new_btn)

        layout.addWidget(self._header)

        # 内容容器（用于放置 scroll 和 empty_state，共享同一空间）
        self._content_container = QWidget()
        content_layout = QVBoxLayout(self._content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

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
        content_layout.addWidget(scroll)

        # 空状态界面（完全居中显示）
        self._empty_state = QWidget()

        empty_outer_layout = QVBoxLayout(self._empty_state)
        empty_outer_layout.setContentsMargins(0, 0, 0, 0)
        empty_outer_layout.setSpacing(0)

        empty_outer_layout.addStretch(1)

        self._center_new_btn = PrimaryPushButton(FluentIcon.ADD, "新建项目")
        self._center_new_btn.setFixedSize(140, 44)
        self._center_new_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._center_new_btn.clicked.connect(self._on_new_project)
        empty_outer_layout.addWidget(self._center_new_btn, 0, Qt.AlignmentFlag.AlignHCenter)

        empty_outer_layout.addStretch(1)

        content_layout.addWidget(self._empty_state, stretch=1)
        self._empty_state.hide()

        # 将内容容器添加到主布局
        layout.addWidget(self._content_container, stretch=1)

    def load_projects(self) -> None:
        """加载并显示所有项目。"""
        # 清空现有卡片
        while self._grid_layout.count():
            item = self._grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        projects = self._service.list_projects()

        # 根据项目数量显示不同界面
        if not projects:
            # 没有项目时：隐藏顶部栏和网格，显示空状态界面（带居中按钮）
            self._header.hide()
            self._grid_container.hide()
            self._empty_state.show()
        else:
            # 有项目时：显示顶部栏（带右上角按钮）和网格，隐藏空状态界面
            self._header.show()
            self._grid_container.show()
            self._empty_state.hide()

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
            project = self._service.create_project(
                name=data["name"],
                resolution=data["resolution"],
                aspect_ratio=data["aspect_ratio"],
                cover_image=data["cover_image"],
            )
            if project is None:
                # 名称重复，提示用户
                QMessageBox.warning(
                    self,
                    "项目名称重复",
                    f"\"{data['name']}\" 已存在"
                )
                return
            self.load_projects()

    def _on_edit_project(self, project_id: int) -> None:
        """编辑项目。"""
        project = self._service.get_project(project_id)
        if not project:
            return

        dialog = ProjectDialog(self, project)
        if dialog.exec():
            data = dialog.get_data()
            success = self._service.update_project(
                project_id=project_id,
                name=data["name"],
                resolution=data["resolution"],
                aspect_ratio=data["aspect_ratio"],
                cover_image=data["cover_image"],
            )
            if not success:
                # 名称重复，提示用户
                QMessageBox.warning(
                    self,
                    "项目名称重复",
                    f"\"{data['name']}\" 已存在"
                )
                return
            self.load_projects()

    def _on_delete_project(self, project_id: int) -> None:
        """删除项目（带随机数字二次确认）。"""
        project = self._service.get_project(project_id)
        if not project:
            return

        # 统计项目关联的素材数量
        db = self._service._db
        media_count = len(db.list_media_files(project_id=project_id))

        # 生成6位随机数字
        verification_code = str(random.randint(100000, 999999))

        # 创建自定义确认对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("确认删除项目")
        dialog.setFixedSize(450, 280)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # 标题
        title = QLabel(f"删除项目：{project.name}")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #E81123;")
        layout.addWidget(title)

        # 警告信息
        warning_text = (
            f"以下数据将被永久删除：\n"
            f"• 项目关联的 {media_count} 个素材文件\n"
            f"• 项目的大纲、剧本、分镜等所有数据\n"
            f"• 项目关联的对话记录\n\n"
            f"此操作不可恢复！"
        )
        warning_label = QLabel(warning_text)
        warning_label.setWordWrap(True)
        warning_label.setStyleSheet("color: #555; font-size: 13px; line-height: 1.6;")
        layout.addWidget(warning_label)

        # 验证码提示
        code_label = QLabel(f"请输入以下数字以确认删除：<b>{verification_code}</b>")
        code_label.setStyleSheet("font-size: 14px; color: #333; margin-top: 8px;")
        layout.addWidget(code_label)

        # 输入框
        from qfluentwidgets import LineEdit
        code_input = LineEdit()
        code_input.setPlaceholderText("输入6位数字")
        code_input.setMaxLength(6)
        layout.addWidget(code_input)

        layout.addStretch()

        # 按钮行
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.setSpacing(12)

        cancel_btn = PushButton("取消")
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)

        delete_btn = PushButton("删除")
        style_button(delete_btn, "danger")
        delete_btn.setEnabled(False)
        btn_layout.addWidget(delete_btn)

        layout.addLayout(btn_layout)

        # 验证输入，只有匹配才启用删除按钮
        def on_text_changed(text: str):
            delete_btn.setEnabled(text == verification_code)

        code_input.textChanged.connect(on_text_changed)
        delete_btn.clicked.connect(dialog.accept)

        # 显示对话框
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                self._service.delete_project(project_id)
                QMessageBox.information(self, "成功", f"项目 \"{project.name}\" 已删除")
                self.load_projects()
            except Exception as e:
                logger.exception("删除项目失败")
                QMessageBox.critical(self, "错误", f"删除项目失败：{e}")
