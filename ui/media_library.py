"""素材库页面：网格缩略图视图，支持筛选、搜索、导入和删除。"""

from __future__ import annotations

from loguru import logger
import os
from typing import Callable

from PyQt6.QtCore import QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    ComboBox,
    LineEdit,
    PrimaryPushButton,
    PushButton,
    MessageBox,
    RoundMenu,
    Action,
    FluentIcon,
)

from models.data_models import MediaFile, MediaType
from service.media_service import MediaService, supported_extensions
from ui.page_header import PageHeader
from ui.styles import (
    COLOR_MEDIA_AUDIO,
    COLOR_MEDIA_IMAGE,
    COLOR_MEDIA_VIDEO,
    COLOR_TEXT_SECONDARY,
    style_button,
)

_THUMB_SIZE = QSize(160, 120)
_CARD_WIDTH = 176
_H_SPACING = 12
_GRID_MARGIN = 16

_TYPE_LABELS: dict[str, tuple[str, str]] = {
    "video": ("视频", COLOR_MEDIA_VIDEO),
    "image": ("图片", COLOR_MEDIA_IMAGE),
    "audio": ("音频", COLOR_MEDIA_AUDIO),
}

_MEDIA_ICONS: dict[MediaType, str] = {
    MediaType.VIDEO: "🎬",
    MediaType.IMAGE: "🖼️",
    MediaType.AUDIO: "🎵",
}

def _format_size(size_bytes: int) -> str:
    if size_bytes <= 0:
        return ""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    if size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

class _MediaCard(QWidget):
    """单个素材卡片：缩略图 + 文件名 + 类型标签 + 元信息。"""

    double_clicked = pyqtSignal(str)
    delete_requested = pyqtSignal(str)
    jump_to_conversation = pyqtSignal(str, str)  # conversation_id, message_id
    selection_changed = pyqtSignal()

    def __init__(
        self,
        media: MediaFile,
        on_open_folder: Callable[[str], None],
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.media = media
        self._on_open_folder = on_open_folder
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setFixedWidth(_CARD_WIDTH)
        self.setStyleSheet(
            """
            _MediaCard {
                background-color: #FFFFFF;
                border: 1px solid #E8E8E8;
                border-radius: 8px;
            }
            _MediaCard:hover {
                border-color: #4A90D9;
            }
            """
        )
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 6)
        layout.setSpacing(4)

        # 缩略图区域
        self._thumb_label = QLabel()
        self._thumb_label.setFixedSize(_THUMB_SIZE)
        self._thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._thumb_label.setStyleSheet(
            "background-color: #F0F0F0; border-radius: 6px;"
        )
        self._render_thumbnail()
        layout.addWidget(self._thumb_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        # 文件信息区域
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        # 文件名 + 复选框
        name_row = QHBoxLayout()
        name_row.setSpacing(4)

        self._checkbox = QCheckBox()
        self._checkbox.stateChanged.connect(self.selection_changed.emit)
        name_row.addWidget(self._checkbox)

        name_label = QLabel(self.media.filename)
        name_label.setToolTip(self.media.filename)
        name_label.setStyleSheet("font-size: 12px; color: #333333;")
        name_label.setMaximumWidth(_CARD_WIDTH - 40)
        name_label.setWordWrap(False)
        fm = name_label.fontMetrics()
        elided = fm.elidedText(self.media.filename, Qt.TextElideMode.ElideRight, _CARD_WIDTH - 50)
        name_label.setText(elided)
        name_row.addWidget(name_label, stretch=1)
        info_layout.addLayout(name_row)

        # 类型标签 + 大小
        meta_row = QHBoxLayout()
        meta_row.setSpacing(4)

        type_key = self.media.media_type.value
        type_text, type_color = _TYPE_LABELS.get(type_key, ("文件", "#888"))
        type_badge = QLabel(type_text)
        type_badge.setStyleSheet(
            f"background-color: {type_color}; color: white; "
            f"border-radius: 3px; padding: 1px 6px; font-size: 10px;"
        )
        type_badge.setFixedHeight(16)
        meta_row.addWidget(type_badge)

        size_text = _format_size(self.media.file_size)
        if size_text:
            size_label = QLabel(size_text)
            size_label.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 11px;")
            meta_row.addWidget(size_label)
        meta_row.addStretch()
        info_layout.addLayout(meta_row)

        # 日期
        date_label = QLabel(self.media.created_at.strftime("%Y-%m-%d %H:%M"))
        date_label.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 11px;")
        info_layout.addWidget(date_label)

        layout.addLayout(info_layout)

    def _render_thumbnail(self) -> None:
        media_type = self.media.media_type
        if media_type == MediaType.IMAGE and os.path.exists(self.media.local_path):
            pixmap = QPixmap(self.media.local_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    _THUMB_SIZE,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self._thumb_label.setPixmap(scaled)
                return

        if (
            media_type == MediaType.VIDEO
            and self.media.thumbnail_path
            and os.path.exists(self.media.thumbnail_path)
        ):
            pm = QPixmap(self.media.thumbnail_path).scaled(
                _THUMB_SIZE,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._paint_video_overlays(pm)
            self._thumb_label.setPixmap(pm)
            return

        # 兜底：使用图标
        icon = _MEDIA_ICONS.get(media_type, "📄")
        self._thumb_label.setText(f"<span style='font-size: 48px;'>{icon}</span>")
        self._thumb_label.setTextFormat(Qt.TextFormat.RichText)

    def _paint_video_overlays(self, pm: QPixmap) -> None:
        """在视频缩略图上叠加时长（右下角）。"""
        painter = QPainter(pm)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        font = QFont("Segoe UI", 8, QFont.Weight.Bold)
        painter.setFont(font)
        fm = painter.fontMetrics()
        pad_x, pad_y = 4, 2

        # 右下角：时长
        if self.media.duration > 0:
            dur_text = self._format_duration(self.media.duration)
            tw = fm.horizontalAdvance(dur_text)
            th = fm.height()
            x = pm.width() - tw - pad_x * 2
            y = pm.height() - th - pad_y * 2
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(0, 0, 0, 160))
            painter.drawRoundedRect(x - pad_x, y - pad_y, tw + pad_x * 2, th + pad_y * 2, 3, 3)
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(x, y + fm.ascent(), dur_text)

        painter.end()

    @staticmethod
    def _format_duration(seconds: float) -> str:
        total = int(seconds)
        if total >= 3600:
            return f"{total // 3600}:{total % 3600 // 60:02d}:{total % 60:02d}"
        return f"{total // 60}:{total % 60:02d}"

    def is_selected(self) -> bool:
        return self._checkbox.isChecked()

    def set_selected(self, selected: bool) -> None:
        self._checkbox.setChecked(selected)

    def mouseDoubleClickEvent(self, event) -> None:
        self.double_clicked.emit(self.media.id)

    def contextMenuEvent(self, event) -> None:
        menu = RoundMenu(parent=self)
        play_action = Action(FluentIcon.PLAY, "播放/预览")
        folder_action = Action(FluentIcon.FOLDER, "打开文件夹")

        # 只有来自任务的素材才显示"跳转到对话"
        if self.media.source == "task" and self.media.conversation_id and self.media.message_id:
            jump_action = Action(FluentIcon.CHAT, "跳转到对话")
            jump_action.triggered.connect(
                lambda: self._handle_jump_action(self.media.conversation_id, self.media.message_id)
            )
            menu.addAction(jump_action)
            menu.addSeparator()

        # 连接其他动作的信号
        play_action.triggered.connect(lambda: self.double_clicked.emit(self.media.id))
        folder_action.triggered.connect(lambda: self._on_open_folder(self.media.local_path))

        menu.addAction(play_action)
        menu.addAction(folder_action)
        menu.addSeparator()

        delete_action = Action(FluentIcon.DELETE, "删除")
        delete_action.triggered.connect(lambda: self.delete_requested.emit(self.media.id))
        menu.addAction(delete_action)

        menu.exec(self.mapToGlobal(event.pos()))

    def _handle_jump_action(self, conv_id: str, msg_id: str) -> None:
        """处理跳转动作"""
        self.jump_to_conversation.emit(conv_id, msg_id)

class _EmptyState(QWidget):
    """素材库为空时显示的引导页面。"""

    import_clicked = pyqtSignal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)

        icon_label = QLabel("📁")
        icon_label.setStyleSheet("font-size: 64px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        text_label = QLabel("还没有素材")
        text_label.setStyleSheet("font-size: 16px; color: #888888;")
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(text_label)

        hint_label = QLabel("生成视频后会自动出现在这里，也可以手动导入")
        hint_label.setStyleSheet("font-size: 13px; color: #AAAAAA;")
        hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint_label)

        import_btn = PrimaryPushButton(FluentIcon.DOWNLOAD, "导入文件")
        import_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        import_btn.clicked.connect(self.import_clicked.emit)
        layout.addWidget(import_btn, alignment=Qt.AlignmentFlag.AlignCenter)

class MediaLibrary(QWidget):
    """素材库页面组件。"""

    jump_to_conversation_requested = pyqtSignal(str, str)  # conversation_id, message_id
    back_clicked = pyqtSignal()

    def __init__(
        self,
        media_service: MediaService,
        on_play: Callable[[str], None],
        on_open_folder: Callable[[str], None],
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setObjectName("mediaLibrary")
        self._service = media_service
        self._on_play = on_play
        self._on_open_folder = on_open_folder
        self._cards: list[_MediaCard] = []
        self._current_type: str | None = None
        self._current_keyword: str | None = None
        self._current_project_id: int | None = None
        self._current_files: list[MediaFile] = []
        self._setup_ui()
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._apply_search)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── 顶部标题栏 ──
        self._header = PageHeader("素材库", show_back=False)
        self._header.set_back_tooltip("返回项目详情")
        self._header.back_clicked.connect(self.back_clicked.emit)

        self._type_filter = ComboBox()
        self._type_filter.addItems(["全部", "视频", "图片", "音频"])
        self._type_filter.currentIndexChanged.connect(self._on_type_changed)
        self._header.add_action(self._type_filter)

        self._search_box = LineEdit()
        self._search_box.setPlaceholderText("🔍 搜索文件名…")
        self._search_box.textChanged.connect(self._on_search_text_changed)
        self._header.add_action(self._search_box)

        self._import_btn = PrimaryPushButton(FluentIcon.DOWNLOAD, "导入文件")
        self._import_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._import_btn.clicked.connect(self._on_import)
        self._header.add_action(self._import_btn)

        self._delete_btn = PushButton(FluentIcon.DELETE, "删除选中")
        self._delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        style_button(self._delete_btn, "danger")
        self._delete_btn.setEnabled(False)
        self._delete_btn.clicked.connect(self._on_delete_selected)
        self._header.add_action(self._delete_btn)

        layout.addWidget(self._header)

        # ── 内容区域（网格 + 空状态） ──
        self._stack = QStackedWidget()

        # 网格滚动区域
        self._scroll = QScrollArea()
        self._scroll.setObjectName("mediaScroll")
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self._grid_container = QWidget()
        self._grid_container.setObjectName("mediaGridContainer")
        self._grid_layout = QGridLayout(self._grid_container)
        self._grid_layout.setContentsMargins(_GRID_MARGIN, _GRID_MARGIN, _GRID_MARGIN, _GRID_MARGIN)
        self._grid_layout.setHorizontalSpacing(_H_SPACING)
        self._grid_layout.setVerticalSpacing(12)
        self._grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self._scroll.setWidget(self._grid_container)
        self._stack.addWidget(self._scroll)  # index 0

        # 空状态
        self._empty = _EmptyState()
        self._empty.import_clicked.connect(self._on_import)
        self._stack.addWidget(self._empty)  # index 1

        layout.addWidget(self._stack, stretch=1)

        # ── 底部状态栏 ──
        status_bar = QWidget()
        status_bar.setObjectName("mediaStatusBar")
        status_bar.setFixedHeight(28)
        sb_layout = QHBoxLayout(status_bar)
        sb_layout.setContentsMargins(16, 0, 16, 0)

        self._status_label = QLabel("")
        self._status_label.setObjectName("statusBarLabel")
        sb_layout.addWidget(self._status_label)
        sb_layout.addStretch()

        layout.addWidget(status_bar)

    # ───────── 公共方法 ─────────

    def load_files(self, project_id: int | None = None) -> None:
        """加载素材文件，可选按项目过滤。"""
        self._current_project_id = project_id
        self._header.set_back_visible(bool(project_id))
        self.refresh()

    def refresh(self) -> None:
        """刷新素材列表。"""
        files = self._service.list_files(
            media_type=self._current_type,
            keyword=self._current_keyword,
            project_id=self._current_project_id,
        )
        self._render_cards(files)

    # ───────── 筛选与搜索 ─────────

    def _on_type_changed(self, index: int) -> None:
        type_map = {0: None, 1: "video", 2: "image", 3: "audio"}
        self._current_type = type_map.get(index)
        self.refresh()

    def _on_search_text_changed(self, text: str) -> None:
        self._search_timer.start(300)

    def _apply_search(self) -> None:
        text = self._search_box.text().strip()
        self._current_keyword = text if text else None
        self.refresh()

    # ───────── 渲染 ─────────

    def _calc_cols(self) -> int:
        available = self._scroll.viewport().width() - 2 * _GRID_MARGIN
        cols = max(1, (available + _H_SPACING) // (_CARD_WIDTH + _H_SPACING))
        return cols

    def _update_spacing(self) -> None:
        """动态计算水平间距，使卡片在可用宽度内均匀分布。"""
        cols = self._calc_cols()
        if cols <= 1:
            self._grid_layout.setHorizontalSpacing(_H_SPACING)
            return
        available = self._scroll.viewport().width() - 2 * _GRID_MARGIN
        spacing = (available - cols * _CARD_WIDTH) / (cols - 1)
        self._grid_layout.setHorizontalSpacing(int(spacing))

    def _relayout_cards(self) -> None:
        self._update_spacing()
        cols = self._calc_cols()
        for i, card in enumerate(self._cards):
            self._grid_layout.removeWidget(card)
        for i, card in enumerate(self._cards):
            self._grid_layout.addWidget(card, i // cols, i % cols)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self._cards:
            self._relayout_cards()

    def _render_cards(self, files: list[MediaFile]) -> None:
        # 清除旧卡片
        for card in self._cards:
            card.setParent(None)
            card.deleteLater()
        self._cards.clear()
        self._current_files = files

        if not files:
            self._stack.setCurrentIndex(1)
            self._update_status_bar(0, 0, 0)
            return

        self._stack.setCurrentIndex(0)
        self._update_spacing()
        cols = self._calc_cols()

        for i, media in enumerate(files):
            card = _MediaCard(media, self._on_open_folder)
            card.double_clicked.connect(self._on_card_double_click)
            card.delete_requested.connect(self._delete_single)
            card.jump_to_conversation.connect(self._on_jump_requested)
            card.selection_changed.connect(self._update_delete_btn)
            self._grid_layout.addWidget(card, i // cols, i % cols)
            self._cards.append(card)

        total_size = sum(f.file_size for f in files)
        self._update_status_bar(len(files), 0, total_size)
        self._update_delete_btn()

    # ───────── 操作 ─────────

    def _on_jump_requested(self, conversation_id: str, message_id: str) -> None:
        """处理卡片的跳转请求并转发信号。"""
        self.jump_to_conversation_requested.emit(conversation_id, message_id)

    def _on_card_double_click(self, media_id: str) -> None:
        for card in self._cards:
            if card.media.id == media_id:
                path = card.media.local_path
                if os.path.exists(path):
                    self._on_play(path)
                break

    def _on_import(self) -> None:
        ext_str = " ".join(f"*{e}" for e in sorted(supported_extensions()))
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择要导入的文件",
            "",
            f"媒体文件 ({ext_str});;所有文件 (*)",
        )
        if not files:
            return
        imported = self._service.import_files(files)
        if imported:
            self.refresh()

    def _on_delete_selected(self) -> None:
        selected = [c for c in self._cards if c.is_selected()]
        if not selected:
            return
        count = len(selected)
        w = MessageBox(
            "确认删除",
            f"确定要删除选中的 {count} 个素材吗？\n文件将从磁盘中永久删除。",
            self
        )
        if not w.exec():
            return
        ids = [c.media.id for c in selected]
        self._service.delete_files(ids)
        self.refresh()

    def _delete_single(self, media_id: str) -> None:
        w = MessageBox(
            "确认删除",
            "确定要删除这个素材吗？\n文件将从磁盘中永久删除。",
            self
        )
        if not w.exec():
            return
        self._service.delete_file(media_id)
        self.refresh()

    def _update_delete_btn(self) -> None:
        has_selection = any(c.is_selected() for c in self._cards)
        self._delete_btn.setEnabled(has_selection)
        selected_count = sum(1 for c in self._cards if c.is_selected())
        if selected_count > 0:
            self._delete_btn.setText(f"🗑  删除选中 ({selected_count})")
        else:
            self._delete_btn.setText("🗑  删除选中")

    def _update_status_bar(self, total: int, selected: int, total_size: int) -> None:
        parts = [f"共 {total} 个素材"]
        if selected > 0:
            parts.append(f"已选 {selected} 个")
        parts.append(f"总大小 {_format_size(total_size)}")
        self._status_label.setText("  |  ".join(parts))
