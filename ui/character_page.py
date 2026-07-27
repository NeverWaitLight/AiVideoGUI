"""角色管理页面：大横卡列表，支持新增、编辑、删除和查看编辑历史。"""

from __future__ import annotations

import logging
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
    ToolButton,
)

from models.data_models import Character, CharacterHistory
from service.character_service import CharacterService

logger = logging.getLogger(__name__)


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

        save_btn = PrimaryPushButton("保存")
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
            QMessageBox.warning(self, "提示", "角色名不能为空")
            return
        if not ref_code:
            QMessageBox.warning(self, "提示", "引用代号不能为空")
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


class CharacterCard(CardWidget):
    """角色横卡（约 400x120）。"""

    edit_requested = pyqtSignal(str)  # character uuid
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

        # 右侧：操作按钮
        btn_widget = QWidget()
        btn_layout = QVBoxLayout(btn_widget)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(8)

        edit_btn = PushButton("编辑", self, FluentIcon.EDIT)
        edit_btn.setFixedSize(80, 32)
        edit_btn.clicked.connect(lambda: self.edit_requested.emit(self.character.uuid))
        btn_layout.addWidget(edit_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        history_btn = PushButton("历史", self, FluentIcon.HISTORY)
        history_btn.setFixedSize(80, 32)
        history_btn.clicked.connect(lambda: self.history_requested.emit(self.character.uuid))
        btn_layout.addWidget(history_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        main_layout.addWidget(btn_widget, alignment=Qt.AlignmentFlag.AlignVCenter)


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
        add_btn.setFixedSize(120, 36)
        add_btn.clicked.connect(self.add_clicked.emit)
        layout.addWidget(add_btn, alignment=Qt.AlignmentFlag.AlignCenter)


class CharacterPage(QWidget):
    """角色管理页面：大横卡列表。"""

    back_clicked = pyqtSignal()

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

        # ── 顶部工具栏（固定） ──
        toolbar = QWidget()
        toolbar.setFixedHeight(56)
        toolbar.setStyleSheet("background-color: #FAFAFA; border-bottom: 1px solid #E8E8E8;")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(20, 0, 20, 0)
        toolbar_layout.setSpacing(12)

        self._back_btn = ToolButton(FluentIcon.LEFT_ARROW)
        self._back_btn.setFixedSize(36, 36)
        self._back_btn.clicked.connect(self.back_clicked.emit)
        toolbar_layout.addWidget(self._back_btn)

        title = QLabel("角色管理")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        toolbar_layout.addWidget(title, stretch=1)

        self._select_all_cb = CheckBox("全选")
        self._select_all_cb.stateChanged.connect(self._on_select_all_toggled)
        toolbar_layout.addWidget(self._select_all_cb)

        self._add_btn = PrimaryPushButton("新增角色", self, FluentIcon.ADD)
        self._add_btn.clicked.connect(self._on_add)
        toolbar_layout.addWidget(self._add_btn)

        self._delete_selected_btn = PushButton("删除选中", self, FluentIcon.DELETE)
        self._delete_selected_btn.setEnabled(False)
        self._delete_selected_btn.clicked.connect(self._on_delete_selected)
        toolbar_layout.addWidget(self._delete_selected_btn)

        layout.addWidget(toolbar)

        # ── 中间可滚动区域 ──
        self._stacked = QStackedWidget()

        # 卡片网格
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

        # 空状态
        self._empty_state = _EmptyState()
        self._empty_state.add_clicked.connect(self._on_add)
        self._stacked.addWidget(self._empty_state)

        layout.addWidget(self._stacked, 1)

        # ── 底部状态栏（固定） ──
        status_bar = QWidget()
        status_bar.setFixedHeight(32)
        status_bar.setStyleSheet("background-color: #FAFAFA; border-top: 1px solid #E8E8E8;")
        status_layout = QHBoxLayout(status_bar)
        status_layout.setContentsMargins(20, 0, 20, 0)

        self._status_label = QLabel("共 0 个角色")
        self._status_label.setStyleSheet("color: #888; font-size: 12px;")
        status_layout.addWidget(self._status_label)
        status_layout.addStretch()

        layout.addWidget(status_bar)

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
            card.edit_requested.connect(self._on_edit)
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

    def _on_edit(self, character_uuid: str) -> None:
        """编辑角色。"""
        character = self._character_service.get_character(character_uuid)
        if not character:
            return

        dialog = _CharacterEditDialog(self, character)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self._character_service.update_character(
                character_uuid,
                name=data["name"],
                ref_code=data["ref_code"],
                description=data["description"],
            )
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
