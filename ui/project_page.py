"""项目管理页面：项目列表 + 对话列表 + 聊天区域。"""

from __future__ import annotations

import logging
import random
from datetime import datetime

from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTimer
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidgetItem,
    QSplitter,
    QVBoxLayout,
    QWidget,
    QFormLayout,
    QComboBox,
)
from qfluentwidgets import (
    PrimaryPushButton,
    PushButton,
    ToolButton,
    ListWidget,
    FluentIcon,
    LineEdit,
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


class _ProjectRow(QWidget):
    """项目列表行控件。"""

    delete_clicked = pyqtSignal(str)
    edit_clicked = pyqtSignal(str)

    def __init__(self, project_id: str, name: str, info: str, parent: QWidget | None = None):
        super().__init__(parent)
        self._project_id = project_id
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(0)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        self._name_label = QLabel(name)
        self._name_label.setObjectName("projectRowName")
        self._info_label = QLabel(info)
        self._info_label.setObjectName("projectRowInfo")

        text_layout.addWidget(self._name_label)
        text_layout.addWidget(self._info_label)
        layout.addLayout(text_layout, stretch=1)

        # 编辑按钮
        self._edit_btn = ToolButton(FluentIcon.EDIT)
        self._edit_btn.setFixedSize(28, 28)
        self._edit_btn.setIconSize(QSize(16, 16))
        self._edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._edit_btn.setToolTip("编辑项目")
        self._edit_btn.clicked.connect(lambda: self.edit_clicked.emit(self._project_id))
        layout.addWidget(self._edit_btn, alignment=Qt.AlignmentFlag.AlignVCenter)

        # 删除按钮
        self._delete_btn = ToolButton(FluentIcon.DELETE)
        self._delete_btn.setFixedSize(28, 28)
        self._delete_btn.setIconSize(QSize(16, 16))
        self._delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._delete_btn.setToolTip("删除项目")
        self._delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self._project_id))
        layout.addWidget(self._delete_btn, alignment=Qt.AlignmentFlag.AlignVCenter)

        self.set_selected(False)

    def set_selected(self, selected: bool) -> None:
        if selected:
            self._name_label.setStyleSheet("color: #1A5DAB; font-weight: bold; font-size: 14px;")
            self._info_label.setStyleSheet("color: #5A8FBF; font-size: 11px;")
        else:
            self._name_label.setStyleSheet("color: #333333; font-weight: normal; font-size: 14px;")
            self._info_label.setStyleSheet("color: #999999; font-size: 11px;")

    def update_info(self, info: str) -> None:
        self._info_label.setText(info)


class _ConversationRow(QWidget):
    """对话列表行控件。"""

    delete_clicked = pyqtSignal(str)

    def __init__(self, conv_id: str, title: str, time_text: str, parent: QWidget | None = None):
        super().__init__(parent)
        self._conv_id = conv_id
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(0)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        self._title_label = QLabel(title)
        self._title_label.setObjectName("convRowTitle")
        self._time_label = QLabel(time_text)
        self._time_label.setObjectName("convRowTime")

        text_layout.addWidget(self._title_label)
        text_layout.addWidget(self._time_label)
        layout.addLayout(text_layout, stretch=1)

        self._delete_btn = ToolButton(FluentIcon.DELETE)
        self._delete_btn.setFixedSize(28, 28)
        self._delete_btn.setIconSize(QSize(16, 16))
        self._delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._delete_btn.setToolTip("删除对话")
        self._delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self._conv_id))
        layout.addWidget(self._delete_btn, alignment=Qt.AlignmentFlag.AlignVCenter)

        self.set_selected(False)

    def set_selected(self, selected: bool) -> None:
        if selected:
            self._title_label.setStyleSheet("color: #1A5DAB; font-weight: bold; font-size: 13px;")
            self._time_label.setStyleSheet("color: #5A8FBF; font-size: 11px;")
        else:
            self._title_label.setStyleSheet("color: #333333; font-weight: normal; font-size: 13px;")
            self._time_label.setStyleSheet("color: #999999; font-size: 11px;")


class ProjectPage(QWidget):
    """项目管理页面。"""

    project_selected = pyqtSignal(str)  # project_id
    conversation_selected = pyqtSignal(str, str)  # project_id, conversation_id
    new_conversation_clicked = pyqtSignal(str)  # project_id
    conversation_deleted = pyqtSignal(str)  # conversation_id

    def __init__(self, project_service: ProjectService, parent: QWidget | None = None):
        super().__init__(parent)
        self._service = project_service
        self._current_project_id: str | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧：项目列表
        self._project_panel = self._create_project_panel()
        splitter.addWidget(self._project_panel)

        # 中间：对话列表
        self._conversation_panel = self._create_conversation_panel()
        splitter.addWidget(self._conversation_panel)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([240, 660])

        layout.addWidget(splitter)

    def _create_project_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("projectPanel")
        panel.setFixedWidth(240)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # 新建项目按钮
        new_btn = PrimaryPushButton(FluentIcon.ADD, "新建项目")
        new_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        new_btn.clicked.connect(self._on_new_project)
        layout.addWidget(new_btn)

        # 项目列表
        self.project_list = ListWidget()
        self.project_list.currentItemChanged.connect(self._on_project_item_changed)
        layout.addWidget(self.project_list, stretch=1)

        return panel

    def _create_conversation_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("conversationPanel")
        panel.setFixedWidth(240)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # 项目标题
        self.project_title_label = QLabel("选择项目")
        self.project_title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        layout.addWidget(self.project_title_label)

        # 项目信息
        self.project_info_label = QLabel("")
        self.project_info_label.setStyleSheet("font-size: 12px; color: #666;")
        self.project_info_label.setWordWrap(True)
        layout.addWidget(self.project_info_label)

        # 新建对话按钮
        self.new_conv_btn = PrimaryPushButton(FluentIcon.ADD, "新建对话")
        self.new_conv_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.new_conv_btn.clicked.connect(self._on_new_conversation)
        self.new_conv_btn.setEnabled(False)
        layout.addWidget(self.new_conv_btn)

        # 对话列表
        self.conversation_list = ListWidget()
        self.conversation_list.currentItemChanged.connect(self._on_conversation_item_changed)
        layout.addWidget(self.conversation_list, stretch=1)

        return panel

    def _on_project_item_changed(self, current: QListWidgetItem | None, previous: QListWidgetItem | None) -> None:
        if previous:
            prev_widget = self.project_list.itemWidget(previous)
            if isinstance(prev_widget, _ProjectRow):
                prev_widget.set_selected(False)

        if current:
            curr_widget = self.project_list.itemWidget(current)
            if isinstance(curr_widget, _ProjectRow):
                curr_widget.set_selected(True)
            project_id = current.data(Qt.ItemDataRole.UserRole)
            if project_id:
                self._current_project_id = project_id
                self._load_project_detail(project_id)
                self.project_selected.emit(project_id)

    def _on_conversation_item_changed(self, current: QListWidgetItem | None, previous: QListWidgetItem | None) -> None:
        if previous:
            prev_widget = self.conversation_list.itemWidget(previous)
            if isinstance(prev_widget, _ConversationRow):
                prev_widget.set_selected(False)

        if current:
            curr_widget = self.conversation_list.itemWidget(current)
            if isinstance(curr_widget, _ConversationRow):
                curr_widget.set_selected(True)
            conv_id = current.data(Qt.ItemDataRole.UserRole)
            if conv_id and self._current_project_id:
                self.conversation_selected.emit(self._current_project_id, conv_id)

    def _load_project_detail(self, project_id: str) -> None:
        """加载项目详情和对话列表。"""
        project = self._service.get_project(project_id)
        if not project:
            return

        self.project_title_label.setText(project.name)
        self.project_info_label.setText(f"比例: {project.aspect_ratio}\n分辨率: {project.resolution}")
        self.new_conv_btn.setEnabled(True)

        # 加载对话列表
        self.conversation_list.clear()
        conversations = self._service.list_project_conversations(project_id)
        for conv in conversations:
            time_text = _format_time(conv.created_at)
            self._add_conversation_item(conv.id, conv.title, time_text)

    def _add_conversation_item(self, conv_id: str, title: str, time_text: str) -> None:
        item = QListWidgetItem()
        item.setData(Qt.ItemDataRole.UserRole, conv_id)

        row = _ConversationRow(conv_id, title, time_text)
        row.delete_clicked.connect(self._on_delete_conversation)
        item.setSizeHint(QSize(0, 52))

        self.conversation_list.addItem(item)
        self.conversation_list.setItemWidget(item, row)

    def _on_new_project(self) -> None:
        """新建项目对话框。"""
        dialog = _ProjectDialog(self)
        if dialog.exec():
            name, resolution, aspect_ratio = dialog.get_values()
            project = self._service.create_project(name, resolution, aspect_ratio)
            self._add_project_item(project)
            # 选中新建的项目
            for i in range(self.project_list.count()):
                item = self.project_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == project.id:
                    self.project_list.setCurrentItem(item)
                    break

    def _on_edit_project(self, project_id: str) -> None:
        """编辑项目对话框。"""
        project = self._service.get_project(project_id)
        if not project:
            return

        dialog = _ProjectDialog(self, project)
        if dialog.exec():
            name, resolution, aspect_ratio = dialog.get_values()
            self._service.update_project(project_id, name, resolution, aspect_ratio)
            # 更新列表显示
            for i in range(self.project_list.count()):
                item = self.project_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == project_id:
                    widget = self.project_list.itemWidget(item)
                    if isinstance(widget, _ProjectRow):
                        widget._name_label.setText(name)
                        video_count = self._service.get_project_video_count(project_id)
                        widget.update_info(f"{aspect_ratio} · {resolution} · {video_count} 个视频")
                    break
            # 如果是当前选中的项目，更新详情
            if project_id == self._current_project_id:
                self._load_project_detail(project_id)

    def _on_delete_project(self, project_id: str) -> None:
        """删除项目确认对话框（带随机数字二次确认）。"""
        project = self._service.get_project(project_id)
        if not project:
            return

        # 统计项目关联的素材数量
        db = self._service._db
        media_count = len(db.list_media_files(project_id=project_id))

        # 生成6位随机数字
        verification_code = str(random.randint(100000, 999999))

        dlg = QDialog(self.window())
        dlg.setWindowTitle("确认删除项目")
        dlg.setFixedSize(450, 280)

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # 标题
        title = QLabel(f"删除项目：{project.name}")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #E81123;")
        layout.addWidget(title)

        # 警告信息
        msg = QLabel(
            f"以下数据将被永久删除：\n"
            f"• 项目关联的 {media_count} 个素材文件\n"
            f"• 项目的大纲、剧本、分镜等所有数据\n"
            f"• 项目关联的对话记录\n\n"
            f"此操作不可恢复！"
        )
        msg.setWordWrap(True)
        msg.setStyleSheet("color: #555; font-size: 13px; line-height: 1.6;")
        layout.addWidget(msg)

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

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.setSpacing(12)

        cancel_btn = PushButton("取消")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet("PushButton { min-width: 100px; min-height: 36px; padding: 6px 20px; }")
        cancel_btn.clicked.connect(dlg.reject)
        btn_row.addWidget(cancel_btn)

        delete_btn = PushButton("删除")
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_btn.setStyleSheet(
            "PushButton { background-color: #E81123; color: white; border: none; "
            "border-radius: 4px; padding: 6px 20px; min-width: 100px; min-height: 36px; font-weight: bold; }"
            "PushButton:hover { background-color: #C50F1F; }"
            "PushButton:pressed { background-color: #A00D1A; }"
            "PushButton:disabled { background-color: #CCCCCC; color: #888888; }"
        )
        delete_btn.setEnabled(False)  # 初始禁用
        btn_row.addWidget(delete_btn)

        layout.addLayout(btn_row)

        # 验证输入，只有匹配才启用删除按钮
        def on_text_changed(text: str):
            delete_btn.setEnabled(text == verification_code)

        code_input.textChanged.connect(on_text_changed)
        delete_btn.clicked.connect(dlg.accept)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                self._service.delete_project(project_id)
                # 从列表移除
                for i in range(self.project_list.count()):
                    item = self.project_list.item(i)
                    if item.data(Qt.ItemDataRole.UserRole) == project_id:
                        self.project_list.takeItem(i)
                        break
                # 清空对话列表
                if self._current_project_id == project_id:
                    self._current_project_id = None
                    self.conversation_list.clear()
                    self.project_title_label.setText("选择项目")
                    self.project_info_label.setText("")
                    self.new_conv_btn.setEnabled(False)

                QMessageBox.information(self, "成功", f"项目 \"{project.name}\" 已删除")
            except Exception as e:
                logger.exception("删除项目失败")
                QMessageBox.critical(self, "错误", f"删除项目失败：{e}")

    def _on_new_conversation(self) -> None:
        """新建对话。"""
        if not self._current_project_id:
            return
        self.new_conversation_clicked.emit(self._current_project_id)

    def _on_delete_conversation(self, conv_id: str) -> None:
        """删除对话确认。"""
        dlg = QDialog(self.window())
        dlg.setWindowTitle("确认删除")
        dlg.setFixedSize(360, 160)

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(12)

        title = QLabel("确认删除对话")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        msg = QLabel("删除后将无法恢复该对话及其所有视频记录，是否继续？")
        msg.setWordWrap(True)
        msg.setStyleSheet("color: #555; font-size: 13px;")
        layout.addWidget(msg)

        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.setSpacing(12)

        delete_btn = PushButton("删除")
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_btn.setStyleSheet(
            "PushButton { background-color: #E81123; color: white; border: none; "
            "border-radius: 4px; padding: 6px 20px; min-width: 80px; min-height: 32px; }"
            "PushButton:hover { background-color: #C50F1F; }"
            "PushButton:pressed { background-color: #A00D1A; }"
        )
        delete_btn.clicked.connect(dlg.accept)
        btn_row.addWidget(delete_btn)

        cancel_btn = PushButton("取消")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet("PushButton { min-width: 80px; min-height: 32px; padding: 6px 20px; }")
        cancel_btn.clicked.connect(dlg.reject)
        btn_row.addWidget(cancel_btn)

        layout.addLayout(btn_row)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.conversation_deleted.emit(conv_id)
            # 从列表移除
            for i in range(self.conversation_list.count()):
                item = self.conversation_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == conv_id:
                    self.conversation_list.takeItem(i)
                    break

    def _add_project_item(self, project: Project) -> None:
        """添加项目到列表。"""
        item = QListWidgetItem()
        item.setData(Qt.ItemDataRole.UserRole, project.id)

        video_count = self._service.get_project_video_count(project.id)
        info = f"{project.aspect_ratio} · {project.resolution} · {video_count} 个视频"
        row = _ProjectRow(project.id, project.name, info)
        row.delete_clicked.connect(self._on_delete_project)
        row.edit_clicked.connect(self._on_edit_project)
        item.setSizeHint(QSize(0, 64))

        self.project_list.insertItem(0, item)
        self.project_list.setItemWidget(item, row)

    def load_projects(self) -> None:
        """加载所有项目。"""
        self.project_list.clear()
        projects = self._service.list_projects()
        for project in projects:
            self._add_project_item(project)

    def add_conversation_to_current_project(self, conv_id: str, title: str) -> None:
        """向当前项目添加对话。"""
        time_text = _format_time(datetime.now())
        self._add_conversation_item(conv_id, title, time_text)

    def update_conversation_title(self, conv_id: str, title: str) -> None:
        """更新对话标题。"""
        for i in range(self.conversation_list.count()):
            item = self.conversation_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == conv_id:
                widget = self.conversation_list.itemWidget(item)
                if isinstance(widget, _ConversationRow):
                    widget._title_label.setText(title)
                break

    def select_conversation(self, conv_id: str) -> None:
        """选中指定对话。"""
        for i in range(self.conversation_list.count()):
            item = self.conversation_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == conv_id:
                self.conversation_list.setCurrentItem(item)
                break


class _ProjectDialog(QDialog):
    """项目创建/编辑对话框。"""

    def __init__(self, parent: QWidget | None = None, project: Project | None = None):
        super().__init__(parent)
        self._project = project
        self.setWindowTitle("编辑项目" if project else "新建项目")
        self.setFixedSize(400, 280)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(16)

        title = QLabel("编辑项目" if self._project else "新建项目")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        # 项目名称
        self.name_input = LineEdit()
        self.name_input.setPlaceholderText("请输入项目名称")
        if self._project:
            self.name_input.setText(self._project.name)
        form_layout.addRow("项目名称:", self.name_input)

        # 画面比例
        self.aspect_ratio_combo = QComboBox()
        self.aspect_ratio_combo.addItems(["16:9", "9:16", "4:3", "3:4"])
        self.aspect_ratio_combo.currentTextChanged.connect(self._on_aspect_ratio_changed)
        form_layout.addRow("画面比例:", self.aspect_ratio_combo)

        # 分辨率
        self.resolution_combo = QComboBox()
        form_layout.addRow("分辨率:", self.resolution_combo)

        # 初始化选择
        if self._project:
            self.aspect_ratio_combo.setCurrentText(self._project.aspect_ratio)
            # 延迟设置分辨率，确保 combo 已填充
            QTimer.singleShot(0, lambda: self._set_initial_resolution(self._project.resolution))
        else:
            self.aspect_ratio_combo.setCurrentText("16:9")

        layout.addLayout(form_layout)
        layout.addStretch()

        # 按钮
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.setSpacing(12)

        save_btn = PrimaryPushButton("保存" if self._project else "创建")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self.accept)
        btn_row.addWidget(save_btn)

        cancel_btn = PushButton("取消")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        layout.addLayout(btn_row)

    def _on_aspect_ratio_changed(self, ratio: str) -> None:
        """画面比例改变时，更新分辨率选项。"""
        self.resolution_combo.clear()
        resolutions = ["480P", "720P", "1080P", "2K", "4K"]
        self.resolution_combo.addItems(resolutions)
        # 默认选择 720P
        self.resolution_combo.setCurrentText("720P")

    def _set_initial_resolution(self, resolution_value: str) -> None:
        """设置初始分辨率。"""
        self.resolution_combo.setCurrentText(resolution_value)

    def get_values(self) -> tuple[str, str, str]:
        """获取表单值。"""
        name = self.name_input.text().strip() or "未命名项目"
        ratio = self.aspect_ratio_combo.currentText()
        resolution = self.resolution_combo.currentText()
        return (name, resolution, ratio)
