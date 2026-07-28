"""剧本编辑器：场次列表视图和场次详情编辑。"""

from __future__ import annotations

from loguru import logger

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
    QTextEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QSplitter,
    QScrollArea,
    QComboBox,
    QLineEdit,
)
from qfluentwidgets import (
    PrimaryPushButton,
    PushButton,
    FluentIcon,
    CardWidget,
)

from models.enums import SceneLocation, SceneTime
from models.scene import Scene
from service.screenplay_service import ScreenplayService
from ui.page_header import PageHeader, create_icon_button
from ui.styles import style_button

class SceneCard(CardWidget):
    """场次卡片：显示场次摘要信息。"""

    scene_clicked = pyqtSignal(int)  # scene_id (整数)

    def __init__(self, scene: Scene, parent: QWidget | None = None):
        super().__init__(parent)
        self._scene = scene
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setFixedHeight(120)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # 场次标题行
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        # 场次号
        scene_number_label = QLabel(f"第 {self._scene.scene_number} 场")
        scene_number_label.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #0078D4;"
        )
        header_layout.addWidget(scene_number_label)

        # 内外景标签
        location_type_text = {
            SceneLocation.INTERIOR: "内景",
            SceneLocation.EXTERIOR: "外景",
            SceneLocation.INTERIOR_EXTERIOR: "内景/外景",
        }.get(self._scene.location_type, "内景")

        location_type_label = QLabel(location_type_text)
        location_type_label.setStyleSheet(
            "font-size: 12px; color: #666; padding: 2px 8px; "
            "background: #E3F2FD; border-radius: 4px;"
        )
        header_layout.addWidget(location_type_label)

        header_layout.addStretch(1)
        layout.addLayout(header_layout)

        # 地点和时间
        info_text = f"{self._scene.location}  -  "
        time_type_text = {
            SceneTime.DAY: "日",
            SceneTime.NIGHT: "夜",
            SceneTime.DAWN: "晨",
            SceneTime.DUSK: "黄昏",
            SceneTime.EVENING: "傍晚",
            SceneTime.CUSTOM: self._scene.time_detail,
        }.get(self._scene.time_type, "日")

        if self._scene.time_detail and self._scene.time_type != SceneTime.CUSTOM:
            info_text += f"{time_type_text}（{self._scene.time_detail}）"
        else:
            info_text += time_type_text

        info_label = QLabel(info_text)
        info_label.setStyleSheet("font-size: 13px; color: #333;")
        layout.addWidget(info_label)

        # 内容预览（前50个字符）
        preview_text = self._scene.content[:50].replace("\n", " ")
        if len(self._scene.content) > 50:
            preview_text += "..."
        preview_label = QLabel(preview_text)
        preview_label.setStyleSheet("font-size: 12px; color: #666;")
        preview_label.setWordWrap(True)
        layout.addWidget(preview_label, stretch=1)

    def mouseReleaseEvent(self, event):
        """点击卡片发射信号。"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.scene_clicked.emit(self._scene.id)
        super().mouseReleaseEvent(event)

class SceneDetailEditor(QWidget):
    """场次详情编辑器。"""

    back_clicked = pyqtSignal()
    save_clicked = pyqtSignal()

    def __init__(self, screenplay_service: ScreenplayService, parent: QWidget | None = None):
        super().__init__(parent)
        self._service = screenplay_service
        self._current_scene: Scene | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 顶部标题栏
        self._header = PageHeader("场次编辑")
        self._header.set_back_tooltip("返回场次列表")
        self._header.back_clicked.connect(self.back_clicked.emit)

        self.save_btn = PushButton("保存")
        style_button(self.save_btn, "save")
        self.save_btn.clicked.connect(self._on_save)
        self._header.add_action(self.save_btn)

        layout.addWidget(self._header)

        # 编辑区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: #F5F5F5; }")

        editor_container = QWidget()
        editor_layout = QVBoxLayout(editor_container)
        editor_layout.setContentsMargins(20, 20, 20, 20)
        editor_layout.setSpacing(16)

        # 场景信息卡片
        info_card = CardWidget()
        info_card_layout = QVBoxLayout(info_card)
        info_card_layout.setContentsMargins(16, 16, 16, 16)
        info_card_layout.setSpacing(12)

        # 场次号（只读）
        scene_number_layout = QHBoxLayout()
        scene_number_layout.addWidget(QLabel("场次号："))
        self.scene_number_label = QLabel("")
        self.scene_number_label.setStyleSheet("font-weight: bold; color: #0078D4;")
        scene_number_layout.addWidget(self.scene_number_label)
        scene_number_layout.addStretch(1)
        info_card_layout.addLayout(scene_number_layout)

        # 内外景选择
        location_type_layout = QHBoxLayout()
        location_type_layout.addWidget(QLabel("内外景："))
        self.location_type_combo = QComboBox()
        self.location_type_combo.addItems(["内景", "外景", "内景/外景"])
        self.location_type_combo.setFixedWidth(150)
        location_type_layout.addWidget(self.location_type_combo)
        location_type_layout.addStretch(1)
        info_card_layout.addLayout(location_type_layout)

        # 地点输入
        location_layout = QHBoxLayout()
        location_layout.addWidget(QLabel("地点："))
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("如：审讯室、老城区街道")
        location_layout.addWidget(self.location_input, stretch=1)
        info_card_layout.addLayout(location_layout)

        # 时间类型选择
        time_type_layout = QHBoxLayout()
        time_type_layout.addWidget(QLabel("时间："))
        self.time_type_combo = QComboBox()
        self.time_type_combo.addItems(["日", "夜", "晨", "黄昏", "傍晚", "自定义"])
        self.time_type_combo.setFixedWidth(150)
        time_type_layout.addWidget(self.time_type_combo)
        time_type_layout.addStretch(1)
        info_card_layout.addLayout(time_type_layout)

        # 详细时间输入
        time_detail_layout = QHBoxLayout()
        time_detail_layout.addWidget(QLabel("详细时间："))
        self.time_detail_input = QLineEdit()
        self.time_detail_input.setPlaceholderText("选填，如：下午3点")
        time_detail_layout.addWidget(self.time_detail_input, stretch=1)
        info_card_layout.addLayout(time_detail_layout)

        editor_layout.addWidget(info_card)

        # 场次内容编辑
        content_label = QLabel("场次内容")
        content_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
        editor_layout.addWidget(content_label)

        self.content_edit = QTextEdit()
        self.content_edit.setPlaceholderText("请输入场次内容（动作描述 + 对话）...")
        self.content_edit.setStyleSheet(
            """
            QTextEdit {
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                line-height: 1.6;
                background: white;
            }
            QTextEdit:focus {
                border: 1px solid #0078D4;
            }
            """
        )
        self.content_edit.setMinimumHeight(300)
        editor_layout.addWidget(self.content_edit, stretch=1)

        scroll.setWidget(editor_container)
        layout.addWidget(scroll, stretch=1)

    def load_scene(self, scene_id: int) -> None:
        """加载场次数据。"""
        self._current_scene = self._service.get_scene(scene_id)
        if not self._current_scene:
            return

        # 更新标题
        self._header.set_title(f"第 {self._current_scene.scene_number} 场")

        # 填充数据
        self.scene_number_label.setText(str(self._current_scene.scene_number))

        # 内外景
        location_type_index = {
            SceneLocation.INTERIOR: 0,
            SceneLocation.EXTERIOR: 1,
            SceneLocation.INTERIOR_EXTERIOR: 2,
        }.get(self._current_scene.location_type, 0)
        self.location_type_combo.setCurrentIndex(location_type_index)

        # 地点
        self.location_input.setText(self._current_scene.location)

        # 时间类型
        time_type_index = {
            SceneTime.DAY: 0,
            SceneTime.NIGHT: 1,
            SceneTime.DAWN: 2,
            SceneTime.DUSK: 3,
            SceneTime.EVENING: 4,
            SceneTime.CUSTOM: 5,
        }.get(self._current_scene.time_type, 0)
        self.time_type_combo.setCurrentIndex(time_type_index)

        # 详细时间
        self.time_detail_input.setText(self._current_scene.time_detail)

        # 内容
        self.content_edit.setPlainText(self._current_scene.content)

    def _on_save(self) -> None:
        """保存场次。"""
        if not self._current_scene:
            return

        # 解析内外景
        location_type_map = [
            SceneLocation.INTERIOR,
            SceneLocation.EXTERIOR,
            SceneLocation.INTERIOR_EXTERIOR,
        ]
        location_type = location_type_map[self.location_type_combo.currentIndex()]

        # 解析时间类型
        time_type_map = [
            SceneTime.DAY,
            SceneTime.NIGHT,
            SceneTime.DAWN,
            SceneTime.DUSK,
            SceneTime.EVENING,
            SceneTime.CUSTOM,
        ]
        time_type = time_type_map[self.time_type_combo.currentIndex()]

        # 获取输入数据
        location = self.location_input.text().strip()
        time_detail = self.time_detail_input.text().strip()
        content = self.content_edit.toPlainText().strip()

        if not location:
            QMessageBox.warning(self, "提示", "请输入地点")
            return

        if not content:
            QMessageBox.warning(self, "提示", "请输入场次内容")
            return

        try:
            self._service.update_scene(
                self._current_scene.id,
                location_type=location_type,
                location=location,
                time_type=time_type,
                time_detail=time_detail,
                content=content,
            )

            QMessageBox.information(self, "成功", "场次已保存")
            self.save_clicked.emit()
            logger.info(f"保存场次：{self._current_scene.id}")

        except Exception as e:
            logger.exception("保存场次失败")
            QMessageBox.critical(self, "错误", f"保存失败：{e}")

class HistoryListItem(QWidget):
    """历史版本列表项（按保存时间戳分组）。"""

    restore_clicked = pyqtSignal(int)  # created_at 时间戳（毫秒）

    def __init__(self, created_at: int, scene_count: int, parent: QWidget | None = None):
        super().__init__(parent)
        self._created_at = created_at
        self._setup_ui(scene_count)

    def _setup_ui(self, scene_count: int) -> None:
        from datetime import datetime

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # 时间标签（毫秒时间戳 → 格式化时间）
        dt = datetime.fromtimestamp(self._created_at / 1000)
        time_text = dt.strftime("%Y-%m-%d %H:%M:%S")
        time_label = QLabel(f"{time_text}（{scene_count} 场）")
        time_label.setStyleSheet("font-size: 13px; color: #666;")
        layout.addWidget(time_label, stretch=1)

        # 恢复按钮
        restore_btn = PushButton("恢复")
        restore_btn.clicked.connect(lambda: self.restore_clicked.emit(self._created_at))
        layout.addWidget(restore_btn)

class ScreenplayEditor(QWidget):
    """剧本编辑器页面：场次列表视图。"""

    back_clicked = pyqtSignal()
    generate_storyboard_clicked = pyqtSignal(int)  # 发送 project_id

    def __init__(
        self,
        screenplay_service: ScreenplayService,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._service = screenplay_service
        self._current_project_id: int | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        # 主布局：堆叠场次列表和场次详情
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 场次列表视图
        self.list_view = self._create_list_view()
        self.main_layout.addWidget(self.list_view)

        # 场次详情编辑器（初始隐藏）
        self.detail_editor = SceneDetailEditor(self._service)
        self.detail_editor.back_clicked.connect(self._on_detail_back)
        self.detail_editor.save_clicked.connect(self._on_detail_saved)
        self.detail_editor.hide()
        self.main_layout.addWidget(self.detail_editor)

    def _create_list_view(self) -> QWidget:
        """创建场次列表视图。"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 顶部标题栏
        self._list_header = PageHeader("剧本编辑")
        self._list_header.set_back_tooltip("返回项目详情")
        self._list_header.back_clicked.connect(self.back_clicked.emit)

        self.generate_storyboard_btn = PushButton("生成分镜")
        self.generate_storyboard_btn.setIcon(FluentIcon.MOVIE)
        style_button(self.generate_storyboard_btn, "generate")
        self.generate_storyboard_btn.clicked.connect(self._on_generate_storyboard)
        self._list_header.add_action(self.generate_storyboard_btn)

        self.save_history_btn = PushButton("保存历史版本")
        self.save_history_btn.setIcon(FluentIcon.SAVE)
        style_button(self.save_history_btn, "save")
        self.save_history_btn.clicked.connect(self._on_save_history)
        self._list_header.add_action(self.save_history_btn)

        self.history_btn = create_icon_button(FluentIcon.HISTORY, "历史版本")
        self.history_btn.clicked.connect(self._on_toggle_history)
        self._list_header.add_action(self.history_btn)

        layout.addWidget(self._list_header)

        # 主内容区：场次列表 + 历史版本
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧：场次列表
        scenes_widget = QWidget()
        scenes_layout = QVBoxLayout(scenes_widget)
        scenes_layout.setContentsMargins(20, 20, 20, 20)
        scenes_layout.setSpacing(12)

        scenes_title = QLabel("场次列表")
        scenes_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
        scenes_layout.addWidget(scenes_title)

        # 场次滚动区域
        self.scenes_scroll = QScrollArea()
        self.scenes_scroll.setWidgetResizable(True)
        self.scenes_scroll.setStyleSheet("QScrollArea { border: none; background: #F5F5F5; }")

        self.scenes_container = QWidget()
        self.scenes_container_layout = QVBoxLayout(self.scenes_container)
        self.scenes_container_layout.setContentsMargins(0, 0, 0, 0)
        self.scenes_container_layout.setSpacing(12)
        self.scenes_container_layout.addStretch(1)

        self.scenes_scroll.setWidget(self.scenes_container)
        scenes_layout.addWidget(self.scenes_scroll, stretch=1)

        # 右侧：历史版本（默认隐藏，通过历史按钮切换显示）
        self._history_widget = QWidget()
        self._history_widget.setFixedWidth(320)
        history_layout = QVBoxLayout(self._history_widget)
        history_layout.setContentsMargins(20, 20, 20, 20)
        history_layout.setSpacing(12)

        history_title = QLabel("历史版本")
        history_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
        history_layout.addWidget(history_title)

        self.history_list = QListWidget()
        self.history_list.setStyleSheet(
            """
            QListWidget {
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                background: white;
            }
            QListWidget::item {
                border-bottom: 1px solid #F0F0F0;
                padding: 0px;
            }
            QListWidget::item:hover {
                background: #F5F5F5;
            }
            QListWidget::item:selected {
                background: #E3F2FD;
            }
            """
        )
        history_layout.addWidget(self.history_list, stretch=1)

        self._history_widget.hide()

        splitter.addWidget(scenes_widget)
        splitter.addWidget(self._history_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        splitter.setSizes([700, 320])

        layout.addWidget(splitter, stretch=1)

        return widget

    def load_script(self, project_id: int, generated_title: str = "", generated_scenes: list[dict] | None = None) -> None:
        """加载项目剧本。

        Args:
            project_id: 项目 ID
            generated_title: AI 生成的剧本标题（可选，已废弃）
            generated_scenes: AI 生成的场次列表（可选）
        """
        self._current_project_id = project_id

        # 如果有生成的场次数据且当前项目无场次，批量创建场次
        if generated_scenes and not self._service.list_scenes(project_id):
            self._service.batch_create_scenes(project_id, generated_scenes)
            logger.info(f"批量创建场次完成：{len(generated_scenes)} 场")

        # 加载场次列表
        self._load_scenes()

        # 加载历史版本
        self._load_history()

        # 显示列表视图
        self.list_view.show()
        self.detail_editor.hide()

    def _load_scenes(self) -> None:
        """加载场次列表。"""
        # 清空现有卡片
        while self.scenes_container_layout.count() > 1:  # 保留最后的 stretch
            item = self.scenes_container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self._current_project_id:
            return

        scenes = self._service.list_scenes(self._current_project_id)

        if not scenes:
            # 显示空状态
            empty_label = QLabel("暂无场次，请从大纲生成剧本")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet("color: #999; padding: 40px; font-size: 14px;")
            self.scenes_container_layout.insertWidget(0, empty_label)
            return

        # 添加场次卡片
        for scene in scenes:
            card = SceneCard(scene)
            card.scene_clicked.connect(self._on_scene_clicked)
            self.scenes_container_layout.insertWidget(
                self.scenes_container_layout.count() - 1, card
            )

    def _load_history(self) -> None:
        """加载历史版本列表（按保存时间戳分组）。"""
        self.history_list.clear()

        if not self._current_project_id:
            return

        timestamps = self._service.list_history_timestamps(self._current_project_id)

        if not timestamps:
            empty_item = QListWidgetItem(self.history_list)
            empty_widget = QLabel("暂无历史版本")
            empty_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_widget.setStyleSheet("color: #999; padding: 20px;")
            empty_item.setSizeHint(empty_widget.sizeHint())
            self.history_list.addItem(empty_item)
            self.history_list.setItemWidget(empty_item, empty_widget)
            return

        for ts in timestamps:
            scenes = self._service.list_history_by_timestamp(self._current_project_id, ts)
            item = QListWidgetItem(self.history_list)
            widget = HistoryListItem(ts, len(scenes))
            widget.restore_clicked.connect(self._on_restore)
            item.setSizeHint(widget.sizeHint())
            self.history_list.addItem(item)
            self.history_list.setItemWidget(item, widget)

    def _on_scene_clicked(self, scene_id: int) -> None:
        """点击场次卡片，进入详情编辑。"""
        self.detail_editor.load_scene(scene_id)
        self.list_view.hide()
        self.detail_editor.show()

    def _on_detail_back(self) -> None:
        """从详情返回列表。"""
        self.detail_editor.hide()
        self.list_view.show()
        # 重新加载场次列表（可能有修改）
        self._load_scenes()

    def _on_detail_saved(self) -> None:
        """场次保存后刷新列表。"""
        pass  # 保存操作已在 detail_editor 中完成

    def _on_toggle_history(self) -> None:
        """切换历史版本面板的显示/隐藏。"""
        self._history_widget.setVisible(not self._history_widget.isVisible())

    def _on_save_history(self) -> None:
        """保存历史版本。"""
        if not self._current_project_id:
            return

        try:
            self._service.save_history(self._current_project_id)
            self._load_history()
            QMessageBox.information(self, "成功", "历史版本已保存")
            logger.info(f"保存剧本历史版本：项目 {self._current_project_id}")

        except Exception as e:
            logger.exception("保存历史版本失败")
            QMessageBox.critical(self, "错误", f"保存失败：{e}")

    def _on_restore(self, created_at: int) -> None:
        """恢复历史版本（按时间戳）。"""
        if not self._current_project_id:
            return

        reply = QMessageBox.question(
            self,
            "确认恢复",
            "确定要恢复到此历史版本吗？当前所有场次将被历史版本覆盖。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            self._service.restore_from_history(self._current_project_id, created_at)

            # 重新加载剧本
            self.load_script(self._current_project_id)

            QMessageBox.information(self, "成功", "已恢复到历史版本")
            logger.info(f"恢复剧本历史版本：时间戳 {created_at}")

        except Exception as e:
            logger.exception("恢复历史版本失败")
            QMessageBox.critical(self, "错误", f"恢复失败：{e}")

    def _on_generate_storyboard(self) -> None:
        """生成分镜按钮点击。"""
        if not self._current_project_id:
            return

        # 检查是否有场次
        scenes = self._service.list_scenes(self._current_project_id)
        if not scenes:
            QMessageBox.warning(self, "提示", "剧本中没有场次，无法生成分镜")
            return

        # 发送信号给主窗口处理
        self.generate_storyboard_clicked.emit(self._current_project_id)

