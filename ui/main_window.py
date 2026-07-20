"""主窗口：组装 UI 与 VideoService，编排完整生成链路。"""

from __future__ import annotations

import logging
import os
import subprocess
from datetime import datetime

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QMessageBox,
    QSplitter,
    QWidget,
    QMainWindow,
)

from config.manager import ConfigManager
from service.chat_service import ChatService
from service.media_service import MediaService
from service.task_polling_service import TaskPollingService
from service.video_service import VideoService, _PROVIDER_REGISTRY
from storage.database import DatabaseManager
from ui.chat_area import ChatArea
from ui.media_library import MediaLibrary
from ui.settings_dialog import SettingsDialog
from ui.sidebar import Sidebar
from ui.styles import apply_fluent_theme
from ui.widgets import VideoStatusCard

logger = logging.getLogger(__name__)


def _format_time(dt: datetime) -> str:
    """将 datetime 格式化为显示时间（今天 HH:MM，其他 MM-DD HH:MM）。"""
    now = datetime.now()
    if dt.date() == now.date():
        return dt.strftime("%H:%M")
    return dt.strftime("%m-%d %H:%M")


def _app_data_dir() -> str:
    root = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
    return os.path.join(root, "ai-video-gui")


class MainWindow(QMainWindow):
    """应用主窗口。"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI 视频生成")
        self.setMinimumSize(960, 640)
        self.resize(1100, 700)

        # 应用 Fluent 主题
        apply_fluent_theme()

        self._current_conversation_id: str | None = None
        self._video_cards: dict[str, VideoStatusCard] = {}

        # ── 初始化基础设施 ──
        data_dir = _app_data_dir()
        os.makedirs(data_dir, exist_ok=True)
        self._db = DatabaseManager(os.path.join(data_dir, "ai-video-gui.db"))
        self._config = ConfigManager(os.path.join(data_dir, "config.json"))

        # VideoService 仅负责对话和任务提交
        self._service = VideoService(self._db, self._config)
        self._chat_service = ChatService(self._config)

        # 素材库服务
        download_dir = self._config.settings.default_download_dir or self._default_download_dir()
        self._media_service = MediaService(self._db, download_dir)

        # 全局任务轮询服务
        temp_dir = self._default_temp_dir()
        self._polling_service = TaskPollingService(
            db=self._db,
            config=self._config,
            download_dir=download_dir,
            temp_dir=temp_dir,
            provider_registry=_PROVIDER_REGISTRY,
        )
        self._polling_service.set_media_service(self._media_service)

        self._setup_ui()
        self._connect_signals()
        self._load_conversations()

        # 启动全局轮询服务
        self._polling_service.start()

    @staticmethod
    def _default_download_dir() -> str:
        home = os.path.expanduser("~")
        return os.path.join(home, "Videos", "AI-Video-GUI")

    @staticmethod
    def _default_temp_dir() -> str:
        return os.path.join(os.environ.get("TEMP", os.path.expanduser("~")), "ai-video-gui")

    # ───────── UI 组装 ─────────

    def _setup_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.sidebar = Sidebar()

        # 右侧内容区域
        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)

        self.chat_area = ChatArea()
        self.media_library = MediaLibrary(
            self._media_service,
            on_play=self._play_video,
            on_open_folder=self._open_folder,
        )

        # 初始显示聊天区域
        content_layout.addWidget(self.chat_area)
        self.chat_area.show()
        content_layout.addWidget(self.media_library)
        self.media_library.hide()

        splitter.addWidget(self.sidebar)
        splitter.addWidget(content)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([240, 860])

        main_layout.addWidget(splitter)

    def _connect_signals(self) -> None:
        self.sidebar.new_conversation_clicked.connect(self._on_new_conversation)
        self.sidebar.conversation_selected.connect(self._on_conversation_selected)
        self.sidebar.conversation_deleted.connect(self._on_conversation_deleted)
        self.sidebar.library_clicked.connect(self._on_library)
        self.sidebar.settings_clicked.connect(self._on_settings)
        self.chat_area.message_sent.connect(self._on_message_sent)

        # 连接素材库信号
        self.media_library.jump_to_conversation_requested.connect(self._on_jump_to_conversation)

        # 连接全局轮询服务信号
        self._polling_service.status_changed.connect(self._on_status_changed)
        self._polling_service.download_progress.connect(self._on_download_progress)
        self._polling_service.task_finished.connect(self._on_task_finished)
        self._polling_service.task_failed.connect(self._on_task_failed)

        self._chat_service.title_ready.connect(self._on_title_ready)

    # ───────── 数据加载 ─────────

    def _load_conversations(self) -> None:
        convs = self._db.list_conversations()
        for conv in convs:
            time_text = conv.created_at.strftime("%Y-%m-%d %H:%M")
            self.sidebar.add_conversation(conv.id, conv.title, time_text, at_top=False)
        if convs:
            latest = convs[0]
            self.sidebar.select_conversation(latest.id)
            self._on_conversation_selected(latest.id)

    def _load_messages(self, conversation_id: str) -> None:
        self.chat_area.clear_messages()
        for msg in self._db.list_messages(conversation_id):
            time_str = _format_time(msg.created_at)
            if msg.role == "user":
                self.chat_area.add_user_message(msg.content, time_str)
            else:
                card = self.chat_area.add_video_card(
                    message_text=msg.content, timestamp=time_str
                )
                self._video_cards[msg.id] = card
                card.open_folder_clicked.connect(self._open_folder)
                if msg.status.value == "completed" and msg.local_path:
                    meta = self._db.get_video_metadata_by_message(msg.id) or {}
                    card.set_completed(
                        msg.local_path,
                        duration=meta.get("duration", 0),
                        width=meta.get("width", 0),
                        height=meta.get("height", 0),
                    )
                    card.play_btn.clicked.connect(lambda _, p=msg.local_path: self._play_video(p))
                elif msg.status.value == "failed":
                    card.set_failed("生成失败")
                else:
                    card.set_generating()
        QTimer.singleShot(0, self.chat_area._scroll_to_bottom)

    # ───────── 侧边栏事件 ─────────

    def _on_new_conversation(self) -> None:
        self.media_library.hide()
        self.chat_area.show()
        provider_name = self._config.settings.default_provider or "dashscope"
        provider_cfg = self._config.get_provider(provider_name)
        model_name = provider_cfg.default_model if provider_cfg else "wan2.7-t2v"

        conv = self._service.create_conversation(provider_name, model_name, "新对话")
        time_text = conv.created_at.strftime("%Y-%m-%d %H:%M")
        self.sidebar.add_conversation(conv.id, conv.title, time_text)
        self.sidebar.select_conversation(conv.id)
        self._current_conversation_id = conv.id
        self.chat_area.set_header(conv.title, model_name)
        self.chat_area.clear_messages()

    def _on_conversation_selected(self, conv_id: str) -> None:
        self.media_library.hide()
        self.chat_area.show()
        self._current_conversation_id = conv_id
        convs = [c for c in self._db.list_conversations() if c.id == conv_id]
        if convs:
            self.chat_area.set_header(convs[0].title, convs[0].model_name)
        self._load_messages(conv_id)

    def _on_conversation_deleted(self, conv_id: str) -> None:
        self._db.delete_conversation(conv_id)
        if self._current_conversation_id == conv_id:
            self._current_conversation_id = None
            self.chat_area.set_header("AI 视频生成", "未选择模型")
            self.chat_area.clear_messages()

    def _on_library(self) -> None:
        self.sidebar.clear_selection()
        self.chat_area.hide()
        self.media_library.show()
        self.media_library.refresh()

    def _on_jump_to_conversation(self, conversation_id: str, message_id: str) -> None:
        """从素材库跳转到对话，并定位到指定消息。"""
        # 切换到聊天区域
        self.media_library.hide()
        self.chat_area.show()

        # 选中对话
        self.sidebar.select_conversation(conversation_id)
        self._current_conversation_id = conversation_id

        # 加载对话和标题
        convs = [c for c in self._db.list_conversations() if c.id == conversation_id]
        if convs:
            self.chat_area.set_header(convs[0].title, convs[0].model_name)

        # 加载消息
        self._load_messages(conversation_id)

        # 定位到目标消息
        self._scroll_to_message(message_id)

    def _on_title_ready(self, conv_id: str, title: str) -> None:
        self._db.update_conversation_title(conv_id, title)
        self.sidebar.update_conversation_title(conv_id, title)
        if conv_id == self._current_conversation_id:
            convs = [c for c in self._db.list_conversations() if c.id == conv_id]
            model_name = convs[0].model_name if convs else ""
            self.chat_area.set_header(title, model_name)

    # ───────── 消息发送 ─────────

    def _on_message_sent(self, text: str, params: dict) -> None:
        if not self._current_conversation_id:
            self._on_new_conversation()

        provider_name = self._config.settings.default_provider or "dashscope"
        provider_cfg = self._config.get_provider(provider_name)
        if not provider_cfg or not provider_cfg.api_key:
            QMessageBox.warning(
                self,
                "未配置 API Key",
                f"请先在设置中配置 {provider_name} 的 API Key。",
            )
            return

        conv_id = self._current_conversation_id
        is_first_message = len(self._db.list_messages(conv_id)) == 0

        now_str = _format_time(datetime.now())
        self.chat_area.add_user_message(text, now_str)
        self._service.add_user_message(conv_id, text)

        if is_first_message:
            self._chat_service.generate_title(conv_id, text)

        try:
            assistant_msg = self._service.submit_task(
                self._current_conversation_id, text, provider_name, params
            )
        except Exception as e:
            logger.exception("提交任务失败")
            card = self.chat_area.add_video_card()
            card.set_failed(str(e))
            return

        card = self.chat_area.add_ai_message_with_card("马上开始生成视频", now_str)
        card.open_folder_clicked.connect(self._open_folder)
        card.set_generating()
        self._video_cards[assistant_msg.id] = card

    # ───────── VideoService 信号 ─────────

    def _on_status_changed(self, message_id: str, status: str) -> None:
        card = self._video_cards.get(message_id)
        if not card:
            return
        if status == "downloading":
            card.set_downloading(0)
        elif status in ("generating", "running", "pending"):
            card.set_generating()

    def _on_download_progress(self, message_id: str, downloaded: int, total: int) -> None:
        card = self._video_cards.get(message_id)
        if not card or total <= 0:
            return
        pct = int(downloaded * 100 / total)
        card.set_downloading(pct)

    def _on_task_finished(self, message_id: str, local_path: str) -> None:
        card = self._video_cards.get(message_id)
        if card:
            meta = self._db.get_video_metadata_by_message(message_id) or {}
            card.set_completed(
                local_path,
                duration=meta.get("duration", 0),
                width=meta.get("width", 0),
                height=meta.get("height", 0),
            )
            card.play_btn.clicked.connect(lambda _, p=local_path: self._play_video(p))

    def _on_task_failed(self, message_id: str, error: str) -> None:
        card = self._video_cards.get(message_id)
        if card:
            card.set_failed(error)

    # ───────── 视频操作 ─────────

    def _play_video(self, path: str) -> None:
        if not path or not os.path.exists(path):
            return
        try:
            os.startfile(path)
        except Exception as e:
            logger.warning("播放视频失败：%s", e)

    def _open_folder(self, path: str) -> None:
        if not path or not os.path.exists(path):
            return
        folder = os.path.dirname(path)
        try:
            subprocess.Popen(f'explorer /select,"{path}"')
        except Exception as e:
            logger.warning("打开文件夹失败：%s", e)
            try:
                os.startfile(folder)
            except Exception:
                pass

    # ───────── 设置 / 生命周期 ─────────

    def _on_settings(self) -> None:
        dialog = SettingsDialog(self._config, self)
        if dialog.exec():
            self._service._providers.clear()
            self._chat_service.reset_provider()
            self._apply_default_provider()

    def _apply_default_provider(self) -> None:
        name = self._config.settings.default_provider or "dashscope"
        cfg = self._config.get_provider(name)
        model = cfg.default_model if cfg else "wan2.7-t2v"
        if self._current_conversation_id:
            self.chat_area.set_header(
                self.chat_area.title_label.text(), model
            )
        # 同步下载目录
        if self._config.settings.default_download_dir:
            download_dir = self._config.settings.default_download_dir
            self._media_service._download_dir = download_dir
            self._polling_service._download_dir = download_dir

    def _scroll_to_message(self, message_id: str) -> None:
        """滚动到指定消息位置并高亮显示。"""
        card = self._video_cards.get(message_id)
        if not card:
            return

        # 延迟滚动，确保布局完成
        QTimer.singleShot(100, lambda: self._do_scroll_to_card(card))

    def _do_scroll_to_card(self, card: VideoStatusCard) -> None:
        """执行滚动到卡片的操作。"""
        scroll_area = self.chat_area.scroll_area
        viewport_height = scroll_area.viewport().height()

        # 获取卡片在滚动区域中的位置
        card_pos = card.mapTo(scroll_area.widget(), card.pos())
        target_y = card_pos.y() - (viewport_height // 2) + (card.height() // 2)

        # 滚动到目标位置
        scroll_area.verticalScrollBar().setValue(max(0, target_y))

        # 短暂高亮效果（只高亮最外层）
        original_style = card.styleSheet()
        card.setStyleSheet(original_style + "\nVideoStatusCard { border: 2px solid #4A90D9; border-radius: 12px; }")
        QTimer.singleShot(1500, lambda: card.setStyleSheet(original_style))

    def closeEvent(self, event) -> None:
        self._polling_service.shutdown()
        self._db.close()
        super().closeEvent(event)
