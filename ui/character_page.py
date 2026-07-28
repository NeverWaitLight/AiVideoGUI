"""角色管理页面：大横卡列表 + 角色详情页，支持新增、编辑、删除、查看历史、AI 生成设计图。"""

from __future__ import annotations

from loguru import logger
import os
from datetime import datetime

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
    QDialog,
    QFileDialog,
    QFormLayout,
)
from qfluentwidgets import (
    CardWidget,
    CheckBox,
    FluentIcon,
    LineEdit,
    ListWidget,
    PrimaryPushButton,
    PushButton,
    TextEdit,
    TitleLabel,
)

from models.character import Character, CharacterHistory
from service.character_service import CharacterService
from ui.page_header import PageHeader
from ui.styles import style_button
from ui.widgets import AlertDialog

class _CharacterEditDialog(QDialog):
    """角色编辑对话框。"""

    def __init__(self, parent: QWidget | None = None, character: Character | None = None):
        super().__init__(parent)
        self._character = character
        self.setWindowTitle("编辑角色" if character else "新增角色")
        self.setMinimumSize(500, 400)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._name_edit = LineEdit()
        self._name_edit.setPlaceholderText("角色名字")
        form.addRow("角色名：", self._name_edit)

        self._ref_code_edit = LineEdit()
        self._ref_code_edit.setPlaceholderText("引用代号，如 CHAR_A")
        form.addRow("引用代号：", self._ref_code_edit)

        self._description_edit = TextEdit()
        self._description_edit.setPlaceholderText(
            "结构化形象描述，每行一个分区：\n"
            "[物种] 人类-黄种人 / 人类-白人 / 人类-黑人 / 动物（橘猫）/ 拟人化动物（兔子）等\n"
            "[外貌] 25岁女性，瓜子脸，柳叶眉\n"
            "[发型] 齐肩黑色直发，中分\n"
            "[发色] 自然黑\n"
            "[瞳色] 深棕色\n"
            "[体型] 165cm，纤细匀称\n"
            "[上装] 白色棉质衬衫\n"
            "[裤子] 深蓝色高腰牛仔裤\n"
            "[鞋袜] 白色帆布鞋\n"
            "[帽子] 无"
        )
        self._description_edit.setMinimumHeight(200)
        form.addRow("形象描述：", self._description_edit)

        layout.addLayout(form)

        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = PushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = PushButton("保存")
        style_button(save_btn, "save")
        save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

        # 填充已有数据
        if self._character:
            self._name_edit.setText(self._character.name)
            self._ref_code_edit.setText(self._character.ref_code)
            self._description_edit.setPlainText(self._character.description)

    def _on_save(self) -> None:
        name = self._name_edit.text().strip()
        ref_code = self._ref_code_edit.text().strip()
        if not name:
            AlertDialog.warning(self, "提示", "角色名不能为空")
            return
        if not ref_code:
            AlertDialog.warning(self, "提示", "引用代号不能为空")
            return
        self.accept()

    def get_data(self) -> dict:
        """获取编辑后的数据。"""
        return {
            "name": self._name_edit.text().strip(),
            "ref_code": self._ref_code_edit.text().strip(),
            "description": self._description_edit.toPlainText().strip(),
        }

class _CharacterHistoryDialog(QDialog):
    """角色编辑历史对话框。"""

    def __init__(self, history: list[CharacterHistory], parent: QWidget | None = None):
        super().__init__(parent)
        self._history = history
        self.setWindowTitle("编辑历史")
        self.setMinimumSize(600, 400)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        if not self._history:
            empty_label = QLabel("暂无编辑历史")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet("color: #888; font-size: 14px;")
            layout.addWidget(empty_label)
            return

        # 历史列表
        self._list_widget = ListWidget()
        self._detail_label = TextEdit()
        self._detail_label.setReadOnly(True)
        self._detail_label.setMinimumHeight(150)

        for h in self._history:
            time_str = datetime.fromtimestamp(h.created_at / 1000).strftime("%Y-%m-%d %H:%M:%S")
            summary = f"{h.name} ({h.ref_code})"
            self._list_widget.addItem(f"{time_str}  —  {summary}")

        self._list_widget.currentRowChanged.connect(self._on_row_changed)
        layout.addWidget(QLabel("历史版本："))
        layout.addWidget(self._list_widget, 1)
        layout.addWidget(QLabel("版本详情："))
        layout.addWidget(self._detail_label, 1)

        # 默认选中第一项
        if self._history:
            self._list_widget.setCurrentRow(0)

    def _on_row_changed(self, row: int) -> None:
        if row < 0 or row >= len(self._history):
            return
        h = self._history[row]
        lines = [
            f"角色名：{h.name}",
            f"引用代号：{h.ref_code}",
            f"形象描述：{h.description}",
        ]
        self._detail_label.setPlainText("\n".join(lines))

class CharacterDetailPage(QWidget):
    """角色详情页：展示角色完整信息，支持 AI 生成 / 上传设计图。"""

    back_clicked = pyqtSignal()
    design_image_generation_requested = pyqtSignal(str, int)  # (character_uuid, project_id)
    saved = pyqtSignal()  # 保存成功后通知列表刷新

    def __init__(self, character_service: CharacterService, parent: QWidget | None = None):
        super().__init__(parent)
        self._character_service = character_service
        self._current_character: Character | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── 顶部标题栏 ──
        self._header = PageHeader("角色详情")
        self._header.back_clicked.connect(self.back_clicked.emit)
        layout.addWidget(self._header)

        # ── 中间可滚动区域 ──
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(24, 16, 24, 16)
        scroll_layout.setSpacing(16)

        # 基本信息卡片
        info_card = CardWidget(scroll_widget)
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(16, 16, 16, 16)
        info_layout.setSpacing(12)

        # 角色名（可编辑）
        info_layout.addWidget(QLabel("角色名："))
        self._name_edit = LineEdit(scroll_widget)
        self._name_edit.setPlaceholderText("角色名字")
        info_layout.addWidget(self._name_edit)

        # 引用代号（可编辑）
        info_layout.addWidget(QLabel("引用代号："))
        self._ref_code_edit = LineEdit(scroll_widget)
        self._ref_code_edit.setPlaceholderText("引用代号，如 CHAR_A")
        info_layout.addWidget(self._ref_code_edit)

        # 形象描述（可编辑）
        info_layout.addWidget(QLabel("形象描述："))
        self._description_text = TextEdit(scroll_widget)
        self._description_text.setPlaceholderText(
            "结构化形象描述，每行一个分区：\n"
            "[物种] 人类-黄种人 / 人类-白人 / 人类-黑人 / 动物（橘猫）/ 拟人化动物（兔子）等\n"
            "[外貌] 25岁女性，瓜子脸，柳叶眉\n"
            "[发型] 齐肩黑色直发，中分\n"
            "[发色] 自然黑\n"
            "[瞳色] 深棕色\n"
            "[体型] 165cm，纤细匀称\n"
            "[上装] 白色棉质衬衫\n"
            "[裤子] 深蓝色高腰牛仔裤\n"
            "[鞋袜] 白色帆布鞋\n"
            "[帽子] 无"
        )
        self._description_text.setMinimumHeight(200)
        info_layout.addWidget(self._description_text)

        scroll_layout.addWidget(info_card)

        # 设计图卡片
        design_card = CardWidget(scroll_widget)
        design_layout = QVBoxLayout(design_card)
        design_layout.setContentsMargins(16, 16, 16, 16)
        design_layout.setSpacing(12)

        design_title = QLabel("角色设计图")
        design_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        design_layout.addWidget(design_title)

        # 设计图预览
        self._design_preview = QLabel()
        self._design_preview.setFixedSize(320, 320)
        self._design_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._design_preview.setStyleSheet(
            "background-color: #F3F3F3; border-radius: 8px; border: 1px solid #E0E0E0;"
        )
        self._design_preview.setText("暂无设计图")
        design_layout.addWidget(self._design_preview)

        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self._generate_design_btn = PushButton("AI 生成", scroll_widget, FluentIcon.IMAGE_EXPORT)
        style_button(self._generate_design_btn, "generate")
        self._generate_design_btn.clicked.connect(self._on_generate_design_image)
        btn_layout.addWidget(self._generate_design_btn)

        self._upload_btn = PushButton("上传图片", scroll_widget, FluentIcon.FOLDER)
        self._upload_btn.clicked.connect(self._on_upload_design_image)
        btn_layout.addWidget(self._upload_btn)

        btn_layout.addStretch()
        design_layout.addLayout(btn_layout)

        scroll_layout.addWidget(design_card)

        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area, 1)

        # ── 保存按钮（固定在底部） ──
        save_btn = PushButton("保存", self, FluentIcon.SAVE)
        style_button(save_btn, "save")
        save_btn.clicked.connect(self._on_save)
        layout.addWidget(save_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def _on_save(self) -> None:
        """保存角色编辑。"""
        if not self._current_character:
            return
        name = self._name_edit.text().strip()
        ref_code = self._ref_code_edit.text().strip()
        if not name:
            AlertDialog.warning(self, "提示", "角色名不能为空")
            return
        if not ref_code:
            AlertDialog.warning(self, "提示", "引用代号不能为空")
            return
        self._character_service.update_character(
            self._current_character.uuid,
            name=name,
            ref_code=ref_code,
            description=self._description_text.toPlainText().strip(),
        )
        self._current_character.name = name
        self._current_character.ref_code = ref_code
        self._current_character.description = self._description_text.toPlainText().strip()
        self._header.set_title(f"角色详情 — {name}")
        self.saved.emit()
        AlertDialog.info(self, "成功", "角色信息已保存！")

    def load_character(self, character_uuid: str) -> None:
        """加载角色数据到详情页。"""
        char = self._character_service.get_character(character_uuid)
        if not char:
            AlertDialog.warning(self, "错误", "角色不存在")
            self.back_clicked.emit()
            return

        self._current_character = char
        self._header.set_title(f"角色详情 — {char.name}")
        self._name_edit.setText(char.name)
        self._ref_code_edit.setText(char.ref_code)
        self._description_text.setPlainText(char.description or "")
        self._update_design_preview(char.design_image or "")

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
        self._design_preview.setStyleSheet(
            "background-color: #F3F3F3; border-radius: 8px; border: 1px solid #E0E0E0; color: #909090;"
        )
        self._design_preview.setText("暂无设计图")

    def set_generating_design(self, generating: bool) -> None:
        """切换设计图生成中状态。"""
        if generating:
            self._generate_design_btn.setEnabled(False)
            self._generate_design_btn.setText("生成中...")
            self._design_preview.clear()
            self._design_preview.setStyleSheet(
                "background-color: #F3F3F3; border-radius: 8px; border: 1px solid #E0E0E0; color: #909090;"
            )
            self._design_preview.setText("正在生成设计图...")
        else:
            self._generate_design_btn.setEnabled(True)
            self._generate_design_btn.setText("AI 生成")

    def set_design_image_result(self, image_path: str) -> None:
        """设计图生成完成回调。"""
        self.set_generating_design(False)
        if image_path:
            self._update_design_preview(image_path)
        elif self._current_character and self._current_character.design_image:
            self._update_design_preview(self._current_character.design_image)

    def _on_generate_design_image(self) -> None:
        """触发 AI 生成设计图。"""
        if not self._current_character:
            return
        if not self._current_character.description:
            AlertDialog.warning(self, "提示", "请先编辑角色形象描述，再生成设计图")
            return
        self.design_image_generation_requested.emit(
            self._current_character.uuid,
            self._current_character.project_id,
        )

    def _on_upload_design_image(self) -> None:
        """上传图片作为设计图。"""
        if not self._current_character:
            return
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择设计图", "", "图片文件 (*.png *.jpg *.jpeg *.webp)"
        )
        if not file_path:
            return
        self._character_service.update_character(
            self._current_character.uuid,
            design_image=file_path,
        )
        self._current_character.design_image = file_path
        self._update_design_preview(file_path)
        self.saved.emit()
        AlertDialog.info(self, "成功", "设计图上传成功！")

class CharacterCard(CardWidget):
    """角色横卡（约 400x120），点击卡片进入详情页。"""

    open_requested = pyqtSignal(str)  # character uuid
    history_requested = pyqtSignal(str)
    delete_requested = pyqtSignal(str)

    def __init__(self, character: Character, parent: QWidget | None = None):
        super().__init__(parent)
        self.character = character
        self._setup_ui()

    @property
    def is_checked(self) -> bool:
        return self._checkbox.isChecked()

    def set_checked(self, checked: bool) -> None:
        self._checkbox.blockSignals(True)
        self._checkbox.setChecked(checked)
        self._checkbox.blockSignals(False)

    def mouseReleaseEvent(self, event):
        """点击卡片任意区域（排除子控件）进入详情。"""
        widget = self.childAt(event.pos())
        if widget in (self._checkbox, self._history_btn):
            super().mouseReleaseEvent(event)
            return
        self.open_requested.emit(self.character.uuid)
        super().mouseReleaseEvent(event)

    def _setup_ui(self) -> None:
        self.setFixedHeight(120)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(16)

        # 勾选框
        self._checkbox = CheckBox()
        self._checkbox.setFixedSize(24, 24)
        main_layout.addWidget(self._checkbox, alignment=Qt.AlignmentFlag.AlignVCenter)

        # 左侧：设计图区域
        image_label = QLabel()
        image_label.setFixedSize(96, 96)
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_label.setStyleSheet(
            "background-color: #F3F3F3; border-radius: 8px; border: 1px solid #E0E0E0;"
        )

        if self.character.design_image:
            pixmap = QPixmap(self.character.design_image)
            if not pixmap.isNull():
                scaled = pixmap.scaled(96, 96, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                image_label.setPixmap(scaled)
            else:
                image_label.setText(self.character.name[:1])
                image_label.setStyleSheet(
                    "background-color: #0078D4; color: white; border-radius: 8px; "
                    "font-size: 32px; font-weight: bold;"
                )
        else:
            image_label.setText(self.character.name[:1] if self.character.name else "?")
            image_label.setStyleSheet(
                "background-color: #0078D4; color: white; border-radius: 8px; "
                "font-size: 32px; font-weight: bold;"
            )
        main_layout.addWidget(image_label, alignment=Qt.AlignmentFlag.AlignVCenter)

        # 中间：信息区域
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(6)

        # 第一行：角色名 + 引用代号徽章
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        name_label = TitleLabel(self.character.name)
        header_layout.addWidget(name_label)

        ref_badge = QLabel(self.character.ref_code)
        ref_badge.setStyleSheet(
            "background-color: #8764B8; color: white; padding: 4px 10px; "
            "border-radius: 10px; font-size: 12px;"
        )
        header_layout.addWidget(ref_badge)

        id_label = QLabel(f"#{self.character.id}")
        id_label.setStyleSheet("color: #999; font-size: 12px;")
        header_layout.addWidget(id_label)

        header_layout.addStretch()
        info_layout.addLayout(header_layout)

        # 第二行：形象描述（截断显示）
        desc = self.character.description or "暂无形象描述"
        if len(desc) > 80:
            desc = desc[:80] + "..."
        desc_label = QLabel(desc)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #404040; font-size: 13px;")
        info_layout.addWidget(desc_label)

        main_layout.addWidget(info_widget, 1)

        # 右侧：历史按钮
        self._history_btn = PushButton("历史", self, FluentIcon.HISTORY)
        self._history_btn.clicked.connect(lambda: self.history_requested.emit(self.character.uuid))
        main_layout.addWidget(self._history_btn, alignment=Qt.AlignmentFlag.AlignVCenter)

class _EmptyState(QWidget):
    """空状态提示。"""

    add_clicked = pyqtSignal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)

        icon_label = QLabel("👤")
        icon_label.setStyleSheet("font-size: 48px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        text_label = QLabel("暂无角色")
        text_label.setStyleSheet("color: #888; font-size: 16px;")
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(text_label)

        hint_label = QLabel("点击「新增角色」手动添加，或在生成分镜时自动提取")
        hint_label.setStyleSheet("color: #AAA; font-size: 13px;")
        hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint_label)

        add_btn = PrimaryPushButton("新增角色")
        add_btn.clicked.connect(self.add_clicked.emit)
        layout.addWidget(add_btn, alignment=Qt.AlignmentFlag.AlignCenter)

class CharacterPage(QWidget):
    """角色管理页面：列表 ↔ 详情页双层导航。"""

    back_clicked = pyqtSignal()
    design_image_generation_requested = pyqtSignal(str, int)  # (character_uuid, project_id)

    def __init__(self, character_service: CharacterService, parent: QWidget | None = None):
        super().__init__(parent)
        self._character_service = character_service
        self._current_project_id: int | None = None
        self._cards: list[CharacterCard] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 顶层 QStackedWidget：0=列表视图, 1=详情视图
        self._page_stacked = QStackedWidget()

        # ── 列表视图 ──
        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(0)

        # 列表顶部标题栏
        self._list_header = PageHeader("角色管理")
        self._list_header.back_clicked.connect(self.back_clicked.emit)

        self._select_all_cb = CheckBox("全选")
        self._select_all_cb.stateChanged.connect(self._on_select_all_toggled)
        self._list_header.add_action(self._select_all_cb)

        self._add_btn = PrimaryPushButton("新增角色", self, FluentIcon.ADD)
        self._add_btn.clicked.connect(self._on_add)
        self._list_header.add_action(self._add_btn)

        self._delete_selected_btn = PushButton("删除选中", self, FluentIcon.DELETE)
        style_button(self._delete_selected_btn, "danger")
        self._delete_selected_btn.setEnabled(False)
        self._delete_selected_btn.clicked.connect(self._on_delete_selected)
        self._list_header.add_action(self._delete_selected_btn)

        list_layout.addWidget(self._list_header)

        # 卡片网格 vs 空状态
        self._stacked = QStackedWidget()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        self._grid_widget = QWidget()
        self._grid_layout = QGridLayout(self._grid_widget)
        self._grid_layout.setContentsMargins(20, 16, 20, 16)
        self._grid_layout.setSpacing(12)
        self._grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        scroll.setWidget(self._grid_widget)
        self._stacked.addWidget(scroll)

        self._empty_state = _EmptyState()
        self._empty_state.add_clicked.connect(self._on_add)
        self._stacked.addWidget(self._empty_state)

        list_layout.addWidget(self._stacked, 1)

        # 底部状态栏
        status_bar = QWidget()
        status_bar.setFixedHeight(32)
        status_bar.setStyleSheet("background-color: #FAFAFA; border-top: 1px solid #E8E8E8;")
        status_layout = QHBoxLayout(status_bar)
        status_layout.setContentsMargins(20, 0, 20, 0)

        self._status_label = QLabel("共 0 个角色")
        self._status_label.setStyleSheet("color: #888; font-size: 12px;")
        status_layout.addWidget(self._status_label)
        status_layout.addStretch()

        list_layout.addWidget(status_bar)

        self._page_stacked.addWidget(list_widget)

        # ── 详情视图 ──
        self.detail_page = CharacterDetailPage(self._character_service)
        self.detail_page.back_clicked.connect(self._on_detail_back)
        self.detail_page.design_image_generation_requested.connect(
            self.design_image_generation_requested.emit
        )
        self.detail_page.saved.connect(self._on_detail_saved)
        self._page_stacked.addWidget(self.detail_page)

        layout.addWidget(self._page_stacked, 1)

    def load_project(self, project_id: int) -> None:
        """加载项目的角色数据。"""
        self._current_project_id = project_id
        self._render_cards()

    def _render_cards(self) -> None:
        """重新渲染角色卡片网格。"""
        # 清理旧卡片
        for card in self._cards:
            self._grid_layout.removeWidget(card)
            card.deleteLater()
        self._cards.clear()

        if not self._current_project_id:
            self._stacked.setCurrentIndex(1)
            return

        characters = self._character_service.list_characters(self._current_project_id)

        if not characters:
            self._stacked.setCurrentIndex(1)
            self._status_label.setText("共 0 个角色")
            return

        self._stacked.setCurrentIndex(0)

        cols = 2
        for i, char in enumerate(characters):
            card = CharacterCard(char)
            card.open_requested.connect(self._on_detail)
            card.history_requested.connect(self._on_history)
            card.delete_requested.connect(self._on_delete_single)
            card._checkbox.stateChanged.connect(self._update_selection_state)

            row = i // cols
            col = i % cols
            self._grid_layout.addWidget(card, row, col)
            self._cards.append(card)

        self._status_label.setText(f"共 {len(characters)} 个角色")

    def _on_add(self) -> None:
        """新增角色。"""
        if not self._current_project_id:
            return

        dialog = _CharacterEditDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self._character_service.create_character(
                project_id=self._current_project_id,
                name=data["name"],
                ref_code=data["ref_code"],
                description=data["description"],
            )
            self._render_cards()

    def _on_detail(self, character_uuid: str) -> None:
        """进入角色详情页。"""
        self.detail_page.load_character(character_uuid)
        self._page_stacked.setCurrentIndex(1)

    def _on_detail_back(self) -> None:
        """从详情页返回列表。"""
        self._page_stacked.setCurrentIndex(0)
        self._render_cards()

    def _on_detail_saved(self) -> None:
        """详情页保存后刷新列表。"""
        self._render_cards()

    def _on_history(self, character_uuid: str) -> None:
        """查看编辑历史。"""
        history = self._character_service.list_history(character_uuid)
        dialog = _CharacterHistoryDialog(history, self)
        dialog.exec()

    def _on_delete_single(self, character_uuid: str) -> None:
        """删除单个角色。"""
        reply = QMessageBox.question(
            self,
            "确认删除",
            "确定要删除该角色吗？此操作不可恢复。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._character_service.delete_character(character_uuid)
            self._render_cards()

    def _on_delete_selected(self) -> None:
        """删除选中的角色。"""
        selected = [c for c in self._cards if c.is_checked]
        if not selected:
            return

        count = len(selected)
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除选中的 {count} 个角色吗？此操作不可恢复。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        for card in selected:
            self._character_service.delete_character(card.character.uuid)
        self._render_cards()

    def _on_select_all_toggled(self, state: int) -> None:
        """全选/取消全选。"""
        checked = state == Qt.CheckState.Checked.value
        for card in self._cards:
            card.set_checked(checked)
        self._delete_selected_btn.setEnabled(checked and len(self._cards) > 0)

    def _update_selection_state(self) -> None:
        """更新选中状态。"""
        checked_count = sum(1 for c in self._cards if c.is_checked)
        total = len(self._cards)
        self._delete_selected_btn.setEnabled(checked_count > 0)
        self._select_all_cb.blockSignals(True)
        self._select_all_cb.setChecked(checked_count == total and total > 0)
        self._select_all_cb.blockSignals(False)
