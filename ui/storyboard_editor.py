"""分镜头编辑器 UI：分镜列表、详情编辑、历史版本管理。"""

import logging
import os
import time

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    CardWidget,
    CheckBox,
    ComboBox,
    DoubleSpinBox,
    FluentIcon,
    LineEdit,
    ListWidget,
    PrimaryPushButton,
    PushButton,
    TextEdit,
    TitleLabel,
    ToolButton,
)

from models.data_models import Scene, Storyboard, ShotSize
from service.screenplay_service import ScreenplayService
from service.storyboard_service import StoryboardService

logger = logging.getLogger(__name__)

_CN_DIGITS = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九"]


def _to_chinese_num(n: int) -> str:
    """将正整数转为中文数字（支持 1-999）。"""
    if n <= 0:
        return str(n)
    if n < 10:
        return _CN_DIGITS[n]
    if n < 20:
        return ("十" if n == 10 else "十" + _CN_DIGITS[n - 10])
    if n < 100:
        tens = n // 10
        ones = n % 10
        result = _CN_DIGITS[tens] + "十"
        if ones:
            result += _CN_DIGITS[ones]
        return result
    # 100+
    hundreds = n // 100
    remainder = n % 100
    result = _CN_DIGITS[hundreds] + "百"
    if remainder == 0:
        return result
    if remainder < 10:
        result += "零" + _CN_DIGITS[remainder]
    else:
        tens = remainder // 10
        ones = remainder % 10
        if tens == 0:
            result += "零"
        else:
            result += _CN_DIGITS[tens] + "十"
        if ones:
            result += _CN_DIGITS[ones]
    return result


class StoryboardCard(CardWidget):
    """分镜卡片（横向大块，120px 高度）"""

    storyboard_clicked = pyqtSignal(int)  # 发送 storyboard_id
    generate_video_clicked = pyqtSignal(int)  # 发送 storyboard_id

    def __init__(self, storyboard: Storyboard, parent=None):
        super().__init__(parent)
        self.storyboard = storyboard
        self._setup_ui()

    @property
    def is_checked(self) -> bool:
        return self._checkbox.isChecked()

    @is_checked.setter
    def is_checked(self, value: bool) -> None:
        self._checkbox.setChecked(value)

    def set_checked(self, checked: bool) -> None:
        """设置勾选状态（不触发信号）。"""
        self._checkbox.blockSignals(True)
        self._checkbox.setChecked(checked)
        self._checkbox.blockSignals(False)

    def _setup_ui(self):
        """初始化 UI"""
        self.setFixedHeight(120)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(12)

        # 勾选框
        self._checkbox = CheckBox()
        self._checkbox.setFixedSize(24, 24)
        main_layout.addWidget(self._checkbox, alignment=Qt.AlignmentFlag.AlignVCenter)

        # 设计图缩略图
        thumb = QLabel()
        thumb.setFixedSize(128, 72)
        thumb.setStyleSheet("background: #E0E0E0; border-radius: 4px;")
        thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if self.storyboard.design_image and os.path.exists(self.storyboard.design_image):
            pixmap = QPixmap(self.storyboard.design_image)
            if not pixmap.isNull():
                scaled = pixmap.scaled(128, 72, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                thumb.setPixmap(scaled)
        main_layout.addWidget(thumb, alignment=Qt.AlignmentFlag.AlignVCenter)

        # 左侧：信息区域（可点击）
        info_widget = QWidget()
        info_widget.setCursor(Qt.CursorShape.PointingHandCursor)
        layout = QVBoxLayout(info_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 第一行：镜头号 + 景别徽章
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        shot_number_label = TitleLabel(
            f"{_to_chinese_num(self.storyboard.scene_number)}场{_to_chinese_num(self.storyboard.shot_number)}镜"
        )
        header_layout.addWidget(shot_number_label)

        # 景别徽章
        shot_size_map = {
            ShotSize.EXTREME_CLOSE_UP: "特写",
            ShotSize.CLOSE_UP: "近景",
            ShotSize.MEDIUM_SHOT: "中景",
            ShotSize.FULL_SHOT: "全景",
            ShotSize.LONG_SHOT: "远景",
            ShotSize.EXTREME_LONG_SHOT: "大远景",
        }
        shot_size_badge = QLabel(shot_size_map.get(self.storyboard.shot_size, "中景"))
        shot_size_badge.setStyleSheet(
            "background-color: #0078D4; color: white; padding: 4px 12px; border-radius: 10px; font-size: 12px;"
        )
        header_layout.addWidget(shot_size_badge)

        header_layout.addStretch()
        layout.addLayout(header_layout)

        # 第二行：运镜方式 + 时长
        info_label = QLabel(f"运镜：{self.storyboard.camera_movement or '固定'}  |  时长：{self.storyboard.duration}秒")
        info_label.setStyleSheet("color: #606060; font-size: 13px;")
        layout.addWidget(info_label)

        # 第三行：画面内容预览（最多 60 字符）
        content_preview = self.storyboard.visual_content[:60] + ("..." if len(self.storyboard.visual_content) > 60 else "")
        content_label = QLabel(content_preview)
        content_label.setWordWrap(True)
        content_label.setStyleSheet("color: #202020; font-size: 14px;")
        layout.addWidget(content_label)

        main_layout.addWidget(info_widget, 1)

        # 右侧：生成视频按钮
        generate_btn = PrimaryPushButton("生成视频", self, FluentIcon.VIDEO)
        generate_btn.setFixedSize(100, 36)
        generate_btn.clicked.connect(lambda: self.generate_video_clicked.emit(self.storyboard.id))
        main_layout.addWidget(generate_btn, alignment=Qt.AlignmentFlag.AlignVCenter)

        # 只在信息区域点击时发送 storyboard_clicked 信号
        info_widget.mousePressEvent = lambda e: None
        info_widget.mouseReleaseEvent = lambda e: self.storyboard_clicked.emit(self.storyboard.id)

    def mouseReleaseEvent(self, event):
        """卡片点击事件（仅用于非按钮区域）"""
        super().mouseReleaseEvent(event)


class StoryboardDetailEditor(QWidget):
    """分镜详情编辑器"""

    back_clicked = pyqtSignal()
    storyboard_saved = pyqtSignal()
    generate_design_image_clicked = pyqtSignal(int)  # storyboard_id
    preview_prompt_clicked = pyqtSignal(int)  # storyboard_id

    def __init__(self, storyboard_service: StoryboardService, media_service=None, parent=None):
        super().__init__(parent)
        self._storyboard_service = storyboard_service
        self._media_service = media_service
        self._current_storyboard_id: int | None = None
        self._setup_ui()

    def _setup_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 顶部：返回按钮 + 标题 + 查看提示词按钮（固定）
        top_layout = QHBoxLayout()
        back_btn = ToolButton(FluentIcon.LEFT_ARROW)
        back_btn.setFixedSize(36, 36)
        back_btn.setIconSize(QSize(18, 18))
        back_btn.setToolTip("返回列表")
        back_btn.clicked.connect(self.back_clicked.emit)
        top_layout.addWidget(back_btn)

        title_label = QLabel("分镜详情编辑")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        top_layout.addWidget(title_label, stretch=1)

        self._preview_prompt_btn = PushButton("查看提示词", self, FluentIcon.DOCUMENT)
        self._preview_prompt_btn.setFixedSize(100, 36)
        self._preview_prompt_btn.clicked.connect(self._on_preview_prompt)
        top_layout.addWidget(self._preview_prompt_btn)

        layout.addLayout(top_layout)

        # 中间滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(16)

        # 分镜信息卡片
        info_card = CardWidget(scroll_widget)
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(16, 16, 16, 16)
        info_layout.setSpacing(12)

        # 场次号 + 分镜号（只读）
        self.scene_shot_label = QLabel("场次/分镜：")
        self.scene_shot_label.setStyleSheet("font-size: 14px; color: #606060;")
        info_layout.addWidget(self.scene_shot_label)

        # 景别选择
        shot_size_layout = QHBoxLayout()
        shot_size_layout.addWidget(QLabel("景别："))
        self.shot_size_combo = ComboBox(scroll_widget)
        self.shot_size_combo.addItems(["特写", "近景", "中景", "全景", "远景", "大远景"])
        self.shot_size_combo.setCurrentIndex(2)  # 默认中景
        shot_size_layout.addWidget(self.shot_size_combo, 1)
        info_layout.addLayout(shot_size_layout)

        # 运镜方式
        camera_layout = QHBoxLayout()
        camera_layout.addWidget(QLabel("运镜方式："))
        self.camera_input = LineEdit(scroll_widget)
        self.camera_input.setPlaceholderText("如：固定、慢推、跟拍、摇镜等")
        camera_layout.addWidget(self.camera_input, 1)
        info_layout.addLayout(camera_layout)

        # 时长
        duration_layout = QHBoxLayout()
        duration_layout.addWidget(QLabel("时长（秒）："))
        self.duration_spin = DoubleSpinBox(scroll_widget)
        self.duration_spin.setRange(0.0, 60.0)
        self.duration_spin.setSingleStep(0.5)
        self.duration_spin.setValue(5.0)
        self.duration_spin.setFixedWidth(120)
        duration_layout.addWidget(self.duration_spin)
        duration_layout.addStretch()
        info_layout.addLayout(duration_layout)

        # 分镜设计图
        design_label = QLabel("设计图：")
        info_layout.addWidget(design_label)

        self._design_preview = QLabel()
        self._design_preview.setFixedSize(240, 135)
        self._design_preview.setStyleSheet("background: #E0E0E0; border-radius: 4px;")
        self._design_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_layout.addWidget(self._design_preview)

        design_btn_layout = QHBoxLayout()
        design_btn_layout.setSpacing(8)
        self._generate_design_btn = PushButton("AI 生成", scroll_widget, FluentIcon.IMAGE_EXPORT)
        self._generate_design_btn.setFixedSize(90, 32)
        self._generate_design_btn.clicked.connect(self._on_generate_design_image)
        design_btn_layout.addWidget(self._generate_design_btn)
        upload_btn = QPushButton("上传图片")
        upload_btn.clicked.connect(self._on_upload_design_image)
        design_btn_layout.addWidget(upload_btn)
        design_btn_layout.addStretch()
        info_layout.addLayout(design_btn_layout)

        scroll_layout.addWidget(info_card)

        # 画面内容编辑
        scroll_layout.addWidget(QLabel("画面内容描述："))
        self.visual_content_edit = TextEdit(scroll_widget)
        self.visual_content_edit.setPlaceholderText("描述镜头中的人物、动作、环境细节...")
        self.visual_content_edit.setMinimumHeight(100)
        scroll_layout.addWidget(self.visual_content_edit)

        # 台词/对白
        scroll_layout.addWidget(QLabel("台词/对白："))
        self.dialogue_edit = TextEdit(scroll_widget)
        self.dialogue_edit.setPlaceholderText("角色对话内容...")
        self.dialogue_edit.setMinimumHeight(80)
        scroll_layout.addWidget(self.dialogue_edit)

        # 音效
        scroll_layout.addWidget(QLabel("音效："))
        self.sound_effect_edit = LineEdit(scroll_widget)
        self.sound_effect_edit.setPlaceholderText("环境音、特效音、背景音乐提示...")
        scroll_layout.addWidget(self.sound_effect_edit)

        # 备注
        scroll_layout.addWidget(QLabel("备注："))
        self.notes_edit = TextEdit(scroll_widget)
        self.notes_edit.setPlaceholderText("其他说明...")
        self.notes_edit.setMinimumHeight(60)
        scroll_layout.addWidget(self.notes_edit)

        # ── 关联视频区块 ──
        video_label = QLabel("关联视频：")
        video_label.setStyleSheet("font-weight: bold; margin-top: 8px;")
        scroll_layout.addWidget(video_label)

        self.video_list_container = QWidget(scroll_widget)
        self.video_list_layout = QVBoxLayout(self.video_list_container)
        self.video_list_layout.setContentsMargins(0, 0, 0, 0)
        self.video_list_layout.setSpacing(8)
        scroll_layout.addWidget(self.video_list_container)

        self.video_empty_label = QLabel("暂无关联视频")
        self.video_empty_label.setStyleSheet("color: #909090; padding: 12px;")
        self.video_empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll_layout.addWidget(self.video_empty_label)

        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area, 1)

        # 保存按钮（固定在底部）
        save_btn = PrimaryPushButton("保存", self, FluentIcon.SAVE)
        save_btn.clicked.connect(self._on_save_storyboard)
        layout.addWidget(save_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def _update_design_preview(self, image_path: str = "") -> None:
        """更新设计图预览。"""
        if image_path and os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    self._design_preview.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self._design_preview.setPixmap(scaled)
                return
        self._design_preview.clear()
        self._design_preview.setStyleSheet("background: #E0E0E0; border-radius: 4px; color: #909090;")
        self._design_preview.setText("暂无设计图")

    def load_storyboard(self, storyboard_id: int):
        """加载分镜数据"""
        self._current_storyboard_id = storyboard_id
        storyboard = self._storyboard_service.get_storyboard(storyboard_id)
        if not storyboard:
            QMessageBox.warning(self, "错误", "分镜不存在")
            self.back_clicked.emit()
            return

        # 填充数据
        self.scene_shot_label.setText(f"场次/分镜：第 {storyboard.scene_number} 场 / 第 {storyboard.shot_number} 镜")

        # 景别
        shot_size_index_map = {
            ShotSize.EXTREME_CLOSE_UP: 0,
            ShotSize.CLOSE_UP: 1,
            ShotSize.MEDIUM_SHOT: 2,
            ShotSize.FULL_SHOT: 3,
            ShotSize.LONG_SHOT: 4,
            ShotSize.EXTREME_LONG_SHOT: 5,
        }
        self.shot_size_combo.setCurrentIndex(shot_size_index_map.get(storyboard.shot_size, 2))

        self.camera_input.setText(storyboard.camera_movement)
        self.duration_spin.setValue(storyboard.duration)
        self._update_design_preview(storyboard.design_image or "")
        self.visual_content_edit.setPlainText(storyboard.visual_content)
        self.dialogue_edit.setPlainText(storyboard.dialogue)
        self.sound_effect_edit.setText(storyboard.sound_effect)
        self.notes_edit.setPlainText(storyboard.notes)

        self._load_video_list()

    def _load_video_list(self):
        """加载并渲染关联视频列表。"""
        # 清空现有视频行
        while self.video_list_layout.count():
            item = self.video_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self._media_service or not self._current_storyboard_id:
            self.video_empty_label.show()
            return

        videos = self._media_service.list_by_storyboard(self._current_storyboard_id)
        if not videos:
            self.video_empty_label.show()
            return

        self.video_empty_label.hide()
        for media in videos:
            row = self._create_video_row(media)
            self.video_list_layout.addWidget(row)

    def _create_video_row(self, media) -> QWidget:
        """创建单个视频行组件。"""
        card = CardWidget(self.video_list_container)
        row_layout = QHBoxLayout(card)
        row_layout.setContentsMargins(12, 8, 12, 8)
        row_layout.setSpacing(10)

        # 封面标记
        if media.featured:
            star_label = QLabel("★")
            star_label.setStyleSheet("color: #f5a623; font-size: 16px;")
            row_layout.addWidget(star_label)

        # 缩略图
        thumb_label = QLabel()
        thumb_label.setFixedSize(64, 48)
        thumb_label.setStyleSheet("background: #e0e0e0; border-radius: 4px;")
        thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if media.thumbnail_path and os.path.exists(media.thumbnail_path):
            from PyQt6.QtGui import QPixmap
            pix = QPixmap(media.thumbnail_path)
            if not pix.isNull():
                thumb_label.setPixmap(pix.scaled(64, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            thumb_label.setText("🎬")
        row_layout.addWidget(thumb_label)

        # 文件名 + 时长 + 分辨率
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        name_label = QLabel(media.filename)
        name_label.setStyleSheet("font-size: 13px; font-weight: 500;")
        info_layout.addWidget(name_label)

        meta_parts = []
        if media.duration > 0:
            mins = int(media.duration) // 60
            secs = int(media.duration) % 60
            meta_parts.append(f"{mins}:{secs:02d}" if mins else f"{secs}s")
        if media.width > 0 and media.height > 0:
            meta_parts.append(f"{media.width}×{media.height}")
        if meta_parts:
            meta_label = QLabel(" · ".join(meta_parts))
            meta_label.setStyleSheet("font-size: 11px; color: #909090;")
            info_layout.addWidget(meta_label)
        row_layout.addLayout(info_layout, 1)

        # 播放按钮
        play_btn = PushButton("播放", card, FluentIcon.PLAY)
        play_btn.setFixedHeight(28)
        play_btn.setFixedWidth(60)
        local_path = media.local_path
        play_btn.clicked.connect(lambda _, p=local_path: self._on_play_video(p))
        row_layout.addWidget(play_btn)

        # 设为封面按钮
        if not media.featured:
            cover_btn = QPushButton("设为封面", card)
            cover_btn.setFixedHeight(28)
            cover_btn.setFixedWidth(70)
            file_id = media.id
            cover_btn.clicked.connect(lambda _, fid=file_id: self._on_set_featured(fid))
            row_layout.addWidget(cover_btn)

        # 删除按钮
        del_btn = PushButton("删除", card, FluentIcon.DELETE)
        del_btn.setFixedHeight(28)
        del_btn.setFixedWidth(60)
        file_id = media.id
        del_btn.clicked.connect(lambda _, fid=file_id: self._on_delete_video(fid))
        row_layout.addWidget(del_btn)

        return card

    def _on_play_video(self, file_path: str):
        """使用系统默认播放器打开视频。"""
        if file_path and os.path.exists(file_path):
            os.startfile(file_path)

    def _on_set_featured(self, file_id: str):
        """将视频设为分镜封面。"""
        if not self._media_service or not self._current_storyboard_id:
            return
        try:
            self._media_service.set_featured(file_id, self._current_storyboard_id)
            self._load_video_list()
        except Exception as e:
            logger.exception("设置封面失败")
            QMessageBox.critical(self, "错误", f"设置封面失败：{e}")

    def _on_delete_video(self, file_id: str):
        """删除关联视频。"""
        reply = QMessageBox.question(
            self,
            "确认删除",
            "确定要删除此视频文件吗？\n文件将从磁盘永久删除。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        if not self._media_service:
            return
        try:
            self._media_service.delete_file(file_id)
            self._load_video_list()
        except Exception as e:
            logger.exception("删除视频失败")
            QMessageBox.critical(self, "错误", f"删除失败：{e}")

    def _on_preview_prompt(self):
        """查看提示词按钮被点击。"""
        if self._current_storyboard_id:
            self.preview_prompt_clicked.emit(self._current_storyboard_id)

    def _on_save_storyboard(self):
        """保存分镜修改"""
        if not self._current_storyboard_id:
            return

        # 景别映射
        shot_size_map = {
            0: ShotSize.EXTREME_CLOSE_UP,
            1: ShotSize.CLOSE_UP,
            2: ShotSize.MEDIUM_SHOT,
            3: ShotSize.FULL_SHOT,
            4: ShotSize.LONG_SHOT,
            5: ShotSize.EXTREME_LONG_SHOT,
        }
        shot_size = shot_size_map[self.shot_size_combo.currentIndex()]

        try:
            self._storyboard_service.update_storyboard(
                storyboard_id=self._current_storyboard_id,
                shot_size=shot_size,
                camera_movement=self.camera_input.text(),
                duration=self.duration_spin.value(),
                visual_content=self.visual_content_edit.toPlainText(),
                dialogue=self.dialogue_edit.toPlainText(),
                sound_effect=self.sound_effect_edit.text(),
                notes=self.notes_edit.toPlainText(),
            )
            QMessageBox.information(self, "成功", "分镜保存成功！")
            self.storyboard_saved.emit()
            self.back_clicked.emit()
        except Exception as e:
            logger.exception("保存分镜失败")
            QMessageBox.critical(self, "错误", f"保存失败：{e}")

    def _on_upload_design_image(self):
        """上传分镜设计图"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择设计图",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp);;所有文件 (*.*)",
        )
        if not file_path:
            return

        # 更新显示
        self._update_design_preview(file_path)

        # 保存到数据库
        if self._current_storyboard_id:
            try:
                self._storyboard_service.update_storyboard(
                    storyboard_id=self._current_storyboard_id,
                    design_image=file_path,
                )
                QMessageBox.information(self, "成功", "设计图上传成功！")
            except Exception as e:
                logger.exception("上传设计图失败")
                QMessageBox.critical(self, "错误", f"上传失败：{e}")

    def _on_generate_design_image(self):
        """AI 生成分镜设计图（发射信号由主窗口处理）。"""
        if not self._current_storyboard_id:
            return

        storyboard = self._storyboard_service.get_storyboard(self._current_storyboard_id)
        if not storyboard:
            QMessageBox.warning(self, "错误", "分镜不存在")
            return

        if not storyboard.visual_content.strip():
            QMessageBox.warning(self, "提示", "分镜画面内容为空，无法生成设计图")
            return

        self._generate_design_btn.setEnabled(False)
        self.generate_design_image_clicked.emit(self._current_storyboard_id)

    def set_generating_design(self, generating: bool) -> None:
        """设置设计图生成中的 UI 状态。"""
        self._generate_design_btn.setEnabled(not generating)
        if generating:
            self._design_preview.clear()
            self._design_preview.setStyleSheet("background: #E0E0E0; border-radius: 4px; color: #909090;")
            self._design_preview.setText("生成中...")

    def set_design_image_result(self, image_path: str) -> None:
        """设计图生成完成后更新显示。"""
        self._generate_design_btn.setEnabled(True)
        if image_path:
            self._update_design_preview(image_path)
        else:
            storyboard = self._storyboard_service.get_storyboard(self._current_storyboard_id) if self._current_storyboard_id else None
            self._update_design_preview(storyboard.design_image if storyboard and storyboard.design_image else "")


class StoryboardEditor(QWidget):
    """分镜编辑器主界面"""

    back_clicked = pyqtSignal()
    preview_prompt_requested = pyqtSignal(int, int)  # storyboard_id, project_id
    video_generation_requested = pyqtSignal(int, int, int, str, int)  # shot_id, scene_number, shot_number, prompt, project_id
    batch_video_generation_requested = pyqtSignal(list)  # list of dict: {shot_id, scene_number, shot_number, prompt, project_id}
    design_image_generation_requested = pyqtSignal(int, int)  # storyboard_id, project_id

    def __init__(self, storyboard_service: StoryboardService, screenplay_service: ScreenplayService, media_service=None, parent=None):
        super().__init__(parent)
        self._storyboard_service = storyboard_service
        self._screenplay_service = screenplay_service
        self._media_service = media_service
        self._current_project_id: int | None = None
        self._scenes: list[Scene] = []
        self._setup_ui()

    def _setup_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 分镜列表视图
        self.list_view = QWidget()
        list_layout = QHBoxLayout(self.list_view)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(0)

        # 左侧：分镜卡片滚动区
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(20, 20, 10, 20)
        left_layout.setSpacing(16)

        # 顶部：返回按钮 + 标题 + 生成所有按钮
        top_layout = QHBoxLayout()
        back_btn = ToolButton(FluentIcon.LEFT_ARROW)
        back_btn.setFixedSize(36, 36)
        back_btn.setIconSize(QSize(18, 18))
        back_btn.setToolTip("返回")
        back_btn.clicked.connect(self.back_clicked.emit)
        top_layout.addWidget(back_btn)

        title_label = QLabel("分镜头脚本")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        top_layout.addWidget(title_label, stretch=1)

        self._generate_all_btn = PrimaryPushButton("生成所有镜头", self, FluentIcon.PLAY)
        self._generate_all_btn.setFixedHeight(36)
        self._generate_all_btn.clicked.connect(self._on_generate_all)
        top_layout.addWidget(self._generate_all_btn)

        # 历史版本按钮
        self._history_btn = ToolButton(FluentIcon.HISTORY)
        self._history_btn.setFixedSize(36, 36)
        self._history_btn.setIconSize(QSize(18, 18))
        self._history_btn.setToolTip("历史版本")
        self._history_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._history_btn.clicked.connect(self._on_toggle_history)
        top_layout.addWidget(self._history_btn)

        left_layout.addLayout(top_layout)

        # 场次过滤 + 批量操作
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("筛选场次："))
        self.scene_filter_combo = ComboBox(self)
        self.scene_filter_combo.addItem("全部场次")
        self.scene_filter_combo.currentIndexChanged.connect(self._on_scene_filter_changed)
        filter_layout.addWidget(self.scene_filter_combo, 1)

        self._select_all_cb = CheckBox("全选")
        self._select_all_cb.toggled.connect(self._on_select_all_toggled)
        filter_layout.addWidget(self._select_all_cb)

        self._delete_selected_btn = PushButton("删除选中", self, FluentIcon.DELETE)
        self._delete_selected_btn.setFixedHeight(32)
        self._delete_selected_btn.setEnabled(False)
        self._delete_selected_btn.clicked.connect(self._on_delete_selected)
        filter_layout.addWidget(self._delete_selected_btn)

        left_layout.addLayout(filter_layout)

        # 分镜卡片列表
        self.shots_scroll = QScrollArea()
        self.shots_scroll.setWidgetResizable(True)
        self.shots_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.shots_container = QWidget()
        self.shots_layout = QVBoxLayout(self.shots_container)
        self.shots_layout.setContentsMargins(0, 0, 0, 0)
        self.shots_layout.setSpacing(12)
        self.shots_layout.addStretch()
        self.shots_scroll.setWidget(self.shots_container)
        left_layout.addWidget(self.shots_scroll)

        list_layout.addWidget(left_widget, 3)

        # 右侧：历史版本列表（默认隐藏，通过历史按钮切换显示）
        self._history_widget = QWidget()
        self._history_widget.setFixedWidth(320)
        self._history_widget.setStyleSheet("background-color: #F5F5F5; border-left: 1px solid #E0E0E0;")
        right_layout = QVBoxLayout(self._history_widget)
        right_layout.setContentsMargins(16, 20, 16, 20)
        right_layout.setSpacing(12)

        history_title = QLabel("历史版本（自动保存）")
        history_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        right_layout.addWidget(history_title)

        self.history_list = ListWidget(self)
        self.history_list.itemClicked.connect(self._on_history_clicked)
        right_layout.addWidget(self.history_list)

        self._history_widget.hide()
        list_layout.addWidget(self._history_widget)

        layout.addWidget(self.list_view)

        # 分镜详情编辑器（初始隐藏）
        self.detail_editor = StoryboardDetailEditor(
            self._storyboard_service, media_service=self._media_service, parent=self
        )
        self.detail_editor.back_clicked.connect(self._on_back_to_list)
        self.detail_editor.storyboard_saved.connect(self._load_storyboards)
        self.detail_editor.generate_design_image_clicked.connect(self._on_generate_design_image)
        self.detail_editor.preview_prompt_clicked.connect(self._on_preview_prompt)
        self.detail_editor.hide()
        layout.addWidget(self.detail_editor)

    def load_project(self, project_id: int, generated_shots: list[dict] | None = None):
        """加载项目分镜"""
        self._current_project_id = project_id
        logger.info(f"加载项目分镜：project_id={project_id}")

        # 加载场次列表（用于过滤器）
        self._scenes = self._screenplay_service.list_scenes(project_id)
        self._populate_scene_filter()

        # 如果有生成的分镜数据且数据库为空，批量创建
        existing_shots = self._storyboard_service.list_storyboards(project_id=project_id)
        if generated_shots and not existing_shots:
            self._import_generated_shots(generated_shots)

        self._load_storyboards()
        self._load_history()

    def _populate_scene_filter(self):
        """填充场次过滤下拉框"""
        self.scene_filter_combo.blockSignals(True)
        self.scene_filter_combo.clear()
        self.scene_filter_combo.addItem("全部场次")
        for scene in self._scenes:
            self.scene_filter_combo.addItem(f"第 {scene.scene_number} 场", userData=scene.scene_number)
        self.scene_filter_combo.blockSignals(False)

    def _on_scene_filter_changed(self):
        """场次过滤变化"""
        self._load_storyboards()

    def _import_generated_shots(self, generated_shots: list[dict]):
        """导入 AI 生成的分镜数据"""
        logger.info(f"导入 {len(generated_shots)} 个生成的分镜")

        # 需要关联场次ID，根据 scene_number 查找
        scene_map = {scene.scene_number: scene for scene in self._scenes}

        storyboards_to_create = []
        for shot_data in generated_shots:
            scene_number = shot_data.get("scene_number", 1)
            scene = scene_map.get(scene_number)
            if not scene:
                logger.warning(f"未找到场次 {scene_number}，跳过分镜 {shot_data.get('shot_number')}")
                continue

            # 解析音效/台词（分离台词和音效）
            sound_dialogue = shot_data.get("sound_dialogue", "")
            dialogue = ""
            sound_effect = ""
            if "：" in sound_dialogue or ":" in sound_dialogue:
                # 简单启发式：如果有冒号，认为是台词
                dialogue = sound_dialogue
            else:
                sound_effect = sound_dialogue

            storyboard = Storyboard(
                scene_number=scene_number,
                shot_number=shot_data["shot_number"],
                scene_id=scene.id,
                shot_size=ShotSize(shot_data["shot_size"]),
                camera_movement=shot_data.get("camera_movement", ""),
                visual_content=shot_data.get("visual_content", ""),
                dialogue=dialogue,
                sound_effect=sound_effect,
                duration=shot_data.get("duration", 5.0),
                notes=shot_data.get("color_lighting", ""),  # 色调/光影作为备注
                created_at=int(time.time() * 1000),
                updated_at=int(time.time() * 1000),
            )
            storyboards_to_create.append(storyboard)

        if storyboards_to_create:
            self._storyboard_service.batch_create_storyboards(storyboards_to_create)
            logger.info(f"成功导入 {len(storyboards_to_create)} 个分镜")

    def _load_storyboards(self):
        """加载分镜列表"""
        if not self._current_project_id:
            return

        # 清空现有卡片
        while self.shots_layout.count() > 1:
            item = self.shots_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._storyboard_cards: list[StoryboardCard] = []
        self._select_all_cb.blockSignals(True)
        self._select_all_cb.setChecked(False)
        self._select_all_cb.blockSignals(False)
        self._delete_selected_btn.setEnabled(False)

        # 根据场次过滤
        scene_number = self.scene_filter_combo.currentData()

        shots = self._storyboard_service.list_storyboards(
            project_id=self._current_project_id,
            scene_number=scene_number,
        )

        for shot in shots:
            card = StoryboardCard(shot, self)
            card.storyboard_clicked.connect(self._on_storyboard_clicked)
            card.generate_video_clicked.connect(self._on_generate_video)
            card._checkbox.toggled.connect(self._on_card_check_changed)
            self._storyboard_cards.append(card)
            self.shots_layout.insertWidget(self.shots_layout.count() - 1, card)

        logger.info(f"加载了 {len(shots)} 个分镜")

    def _on_storyboard_clicked(self, storyboard_id: int):
        """点击分镜卡片，进入详情编辑"""
        logger.info(f"点击分镜：storyboard_id={storyboard_id}")
        self.list_view.hide()
        self.detail_editor.show()
        self.detail_editor.load_storyboard(storyboard_id)

    def _on_preview_prompt(self, storyboard_id: int):
        """预览提示词（从分镜卡片触发）"""
        storyboard = self._storyboard_service.get_storyboard(storyboard_id)
        if not storyboard:
            QMessageBox.warning(self, "错误", "分镜不存在")
            return

        if not storyboard.visual_content.strip():
            QMessageBox.warning(self, "提示", "分镜画面内容为空，无法生成提示词")
            return

        self.preview_prompt_requested.emit(storyboard_id, self._current_project_id)

    def _on_generate_video(self, storyboard_id: int):
        """生成视频（从分镜卡片触发）"""
        logger.info(f"生成视频：storyboard_id={storyboard_id}")

        storyboard = self._storyboard_service.get_storyboard(storyboard_id)
        if not storyboard:
            QMessageBox.warning(self, "错误", "分镜不存在")
            return

        # 构造视频生成提示词（使用画面内容描述）
        prompt = storyboard.visual_content
        if not prompt.strip():
            QMessageBox.warning(self, "提示", "分镜画面内容为空，无法生成视频")
            return

        # 发送信号给主窗口处理视频生成
        self.video_generation_requested.emit(
            storyboard_id,
            storyboard.scene_number,
            storyboard.shot_number,
            prompt,
            self._current_project_id
        )

    def _on_back_to_list(self):
        """返回列表视图"""
        self.detail_editor.hide()
        self.list_view.show()

    def _on_toggle_history(self) -> None:
        """切换历史版本面板的显示/隐藏。"""
        self._history_widget.setVisible(not self._history_widget.isVisible())

    def _on_generate_design_image(self, storyboard_id: int):
        """AI 生成分镜设计图（从详情编辑器触发，转发到主窗口）。"""
        logger.info(f"AI 生成设计图：storyboard_id={storyboard_id}")
        self.design_image_generation_requested.emit(storyboard_id, self._current_project_id)

    def _on_card_check_changed(self, _checked: bool) -> None:
        """单个卡片勾选变化时，更新全选状态和删除按钮。"""
        if not hasattr(self, "_storyboard_cards"):
            return
        checked_count = sum(1 for c in self._storyboard_cards if c.is_checked)
        total = len(self._storyboard_cards)
        self._delete_selected_btn.setEnabled(checked_count > 0)
        self._select_all_cb.blockSignals(True)
        self._select_all_cb.setChecked(checked_count == total and total > 0)
        self._select_all_cb.blockSignals(False)

    def _on_select_all_toggled(self, checked: bool) -> None:
        """全选/取消全选。"""
        if not hasattr(self, "_storyboard_cards"):
            return
        for card in self._storyboard_cards:
            card.set_checked(checked)
        self._delete_selected_btn.setEnabled(checked and len(self._storyboard_cards) > 0)

    def _on_delete_selected(self) -> None:
        """删除选中的分镜。"""
        if not hasattr(self, "_storyboard_cards"):
            return

        selected = [c for c in self._storyboard_cards if c.is_checked]
        if not selected:
            return

        count = len(selected)
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除选中的 {count} 个分镜吗？此操作不可恢复。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            for card in selected:
                self._storyboard_service.delete_storyboard(card.storyboard.id)
            QMessageBox.information(self, "成功", f"已删除 {count} 个分镜")
            self._load_storyboards()
            logger.info(f"批量删除 {count} 个分镜")
        except Exception as e:
            logger.exception("批量删除分镜失败")
            QMessageBox.critical(self, "错误", f"删除失败：{e}")

    def _on_generate_all(self) -> None:
        """生成所有分镜的视频（并行提交）。"""
        if not hasattr(self, "_storyboard_cards") or not self._storyboard_cards:
            QMessageBox.warning(self, "提示", "没有可生成的分镜")
            return

        if not self._current_project_id:
            return

        # 收集所有分镜数据
        shot_list = []
        for card in self._storyboard_cards:
            prompt = card.storyboard.visual_content
            if not prompt.strip():
                continue
            shot_list.append({
                "shot_id": card.storyboard.id,
                "scene_number": card.storyboard.scene_number,
                "shot_number": card.storyboard.shot_number,
                "prompt": prompt,
                "project_id": self._current_project_id,
            })

        if not shot_list:
            QMessageBox.warning(self, "提示", "所有分镜的画面内容均为空，无法生成")
            return

        reply = QMessageBox.question(
            self,
            "确认批量生成",
            f"将一次性提交 {len(shot_list)} 个分镜视频生成任务到供应商。\n所有任务将并行生成，无需等待前一个完成。\n确定继续？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self._generate_all_btn.setEnabled(False)
        self.batch_video_generation_requested.emit(shot_list)

    def _load_history(self):
        """加载历史版本列表（按时间戳分组显示）。"""
        if not self._current_project_id:
            return

        self.history_list.clear()
        self._history_timestamps = self._storyboard_service.list_history_timestamps(
            self._current_project_id
        )

        from datetime import datetime as _dt

        for ts in self._history_timestamps:
            dt = _dt.fromtimestamp(ts / 1000)
            time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            self.history_list.addItem(time_str)

    def _on_history_clicked(self, item):
        """点击历史版本，恢复"""
        if not self._current_project_id:
            return

        reply = QMessageBox.question(
            self,
            "确认恢复",
            f"确定要恢复到版本：{item.text()} 吗？\n当前版本将被保存到历史记录。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        history_index = self.history_list.row(item)
        if (
            hasattr(self, "_history_timestamps")
            and 0 <= history_index < len(self._history_timestamps)
        ):
            ts = self._history_timestamps[history_index]
            try:
                self._storyboard_service.restore_from_history(self._current_project_id, ts)
                QMessageBox.information(self, "成功", "历史版本恢复成功！")
                self._load_storyboards()
                self._load_history()
            except Exception as e:
                logger.exception("恢复历史失败")
                QMessageBox.critical(self, "错误", f"恢复失败：{e}")
