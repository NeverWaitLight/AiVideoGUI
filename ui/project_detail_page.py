"""项目详情页面：剧本、分镜、角色、素材库等模块入口。"""

from __future__ import annotations

import logging
import re

from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
    QGridLayout,
    QScrollArea,
)
from qfluentwidgets import (
    ToolButton,
    FluentIcon,
    CardWidget,
)

from models.data_models import Project
from service.project_service import ProjectService
from storage.database import DatabaseManager

logger = logging.getLogger(__name__)


class ModuleCard(CardWidget):
    """模块入口卡片。"""

    module_clicked = pyqtSignal(str)  # module_name

    def __init__(
        self,
        module_name: str,
        title: str,
        description: str,
        icon: FluentIcon,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._module_name = module_name
        self.setFixedSize(280, 160)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._setup_ui(title, description, icon)

    def _setup_ui(self, title: str, description: str, icon: FluentIcon) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # 图标
        icon_label = QLabel()
        icon_label.setFixedSize(48, 48)
        icon_label.setStyleSheet(
            f"""
            QLabel {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #E3F2FD, stop:1 #BBDEFB);
                border-radius: 24px;
            }}
            """
        )
        layout.addWidget(icon_label)

        # 标题
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        layout.addWidget(title_label)

        # 描述
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("font-size: 13px; color: #666;")
        layout.addWidget(desc_label)

        layout.addStretch()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.module_clicked.emit(self._module_name)
        super().mousePressEvent(event)


class ProjectDetailPage(QWidget):
    """项目详情页面，显示项目信息和各模块入口。"""

    module_selected = pyqtSignal(int, str)  # project_id, module_name
    back_clicked = pyqtSignal()

    def __init__(self, project_service: ProjectService, db: DatabaseManager, parent: QWidget | None = None):
        super().__init__(parent)
        self._service = project_service
        self._db = db
        self._current_project: Project | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 顶部区域：返回按钮 + 项目信息
        header = QWidget()
        header.setStyleSheet("background: white; border-bottom: 1px solid #E0E0E0;")
        header.setFixedHeight(80)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 12, 20, 12)
        header_layout.setSpacing(16)

        # 返回按钮
        back_btn = ToolButton(FluentIcon.RETURN)
        back_btn.setFixedSize(40, 40)
        back_btn.setIconSize(QSize(20, 20))
        back_btn.setToolTip("返回项目列表")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.back_clicked.emit)
        header_layout.addWidget(back_btn)

        # 项目信息
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(4)

        self.project_name_label = QLabel("项目名称")
        self.project_name_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        info_layout.addWidget(self.project_name_label)

        self.project_info_label = QLabel("项目信息")
        self.project_info_label.setStyleSheet("font-size: 13px; color: #666;")
        info_layout.addWidget(self.project_info_label)

        header_layout.addWidget(info_widget, stretch=1)

        layout.addWidget(header)

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: #FAFAFA; }")

        # 模块网格容器
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(20, 20, 20, 20)
        container_layout.setSpacing(20)

        # 模块标题
        section_title = QLabel("项目模块")
        section_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        container_layout.addWidget(section_title)

        # 模块网格
        grid_widget = QWidget()
        self._grid_layout = QGridLayout(grid_widget)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)
        self._grid_layout.setSpacing(20)
        self._grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        # 模块卡片将在 set_project() 中动态生成
        container_layout.addWidget(grid_widget)
        container_layout.addStretch()

        scroll.setWidget(container)
        layout.addWidget(scroll, stretch=1)

    def set_project(self, project_id: int) -> None:
        """设置当前项目并动态生成模块卡片。"""
        project = self._service.get_project(project_id)
        if not project:
            return

        self._current_project = project
        self.project_name_label.setText(project.name)

        # 清空现有卡片
        for i in reversed(range(self._grid_layout.count())):
            widget = self._grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        # 动态构建模块列表
        modules = []

        # 条件添加播放模块
        if self._has_storyboard_videos(project_id):
            modules.append(("play", "播放", "播放项目分镜视频", FluentIcon.PLAY))

        # 添加固定模块
        modules.extend([
            ("outline", "大纲", "编写和管理项目大纲", FluentIcon.EDIT),
            ("script", "剧本", "编写和管理视频剧本", FluentIcon.DOCUMENT),
            ("storyboard", "分镜", "设计视频分镜脚本", FluentIcon.PHOTO),
            ("character", "角色", "管理项目中的角色资料", FluentIcon.PEOPLE),
            ("media", "素材库", "管理项目相关的媒体文件", FluentIcon.FOLDER),
        ])

        # 重新布局（3列网格）
        row, col = 0, 0
        max_cols = 3
        for module_name, title, description, icon in modules:
            card = ModuleCard(module_name, title, description, icon)
            card.module_clicked.connect(self._on_module_clicked)
            self._grid_layout.addWidget(card, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

        # 更新项目信息
        video_count = self._service.get_project_video_count(project_id)
        info_text = f"{project.aspect_ratio} · {project.resolution} · {video_count} 个视频"
        self.project_info_label.setText(info_text)

    def _has_storyboard_videos(self, project_id: int) -> bool:
        """判断项目是否有分镜视频（文件名匹配 场次-镜头-序号.mp4 格式）。"""
        media_files = self._db.list_media_files(project_id=project_id, media_type="video")
        pattern = re.compile(r"^\d+-\d+-\d+\.mp4$")
        return any(pattern.match(m.filename) for m in media_files)

    def _on_module_clicked(self, module_name: str) -> None:
        """模块被点击。"""
        if self._current_project:
            self.module_selected.emit(self._current_project.id, module_name)
