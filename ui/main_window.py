"""主窗口：组装 UI 与 VideoService，编排完整生成链路。"""

from __future__ import annotations

import logging
import os
import subprocess
from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QWidget,
)

from config.manager import ConfigManager
from service.video_service import VideoService
from storage.database import DatabaseManager
from ui.chat_area import ChatArea
from ui.settings_dialog import SettingsDialog
from ui.sidebar import Sidebar
from ui.styles import MAIN_WINDOW_STYLE
from ui.widgets import VideoStatusCard

logger = logging.getLogger(__name__)


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
        self.setStyleSheet(MAIN_WINDOW_STYLE)

        self._current_conversation_id: str | None = None
        self._video_cards: dict[str, VideoStatusCard] = {}

        # ── 初始化基础设施 ──
        data_dir = _app_data_dir()
        os.makedirs(data_dir, exist_ok=True)
        self._db = DatabaseManager(os.path.join(data_dir, "ai-video-gui.db"))
        self._config = ConfigManager(os.path.join(data_dir, "config.json"))
        self._service = VideoService(
            self._db,
            self._config,
            download_dir=self._config.settings.default_download_dir,
        )

        self._setup_ui()
        self._connect_signals()
        self._load_conversations()

    # ───────── UI 组装 ─────────

    def _setup_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.sidebar = Sidebar()
        self.chat_area = ChatArea()

        splitter.addWidget(self.sidebar)
        splitter.addWidget(self.chat_area)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([240, 860])

        main_layout.addWidget(splitter)

    def _connect_signals(self) -> None:
        self.sidebar.new_conversation_clicked.connect(self._on_new_conversation)
        self.sidebar.conversation_selected.connect(self._on_conversation_selected)
        self.sidebar.conversation_deleted.connect(self._on_conversation_deleted)
        self.sidebar.settings_clicked.connect(self._on_settings)
        self.chat_area.message_sent.connect(self._on_message_sent)

        self._service.status_changed.connect(self._on_status_changed)
        self._service.download_progress.connect(self._on_download_progress)
        self._service.task_finished.connect(self._on_task_finished)
        self._service.task_failed.connect(self._on_task_failed)

    # ───────── 数据加载 ─────────

    def _load_conversations(self) -> None:
        for conv in self._db.list_conversations():
            time_text = conv.created_at.strftime("%Y-%m-%d %H:%M")
            self.sidebar.add_conversation(conv.id, conv.title, time_text, at_top=False)

    def _load_messages(self, conversation_id: str) -> None:
        self.chat_area.clear_messages()
        for msg in self._db.list_messages(conversation_id):
            if msg.role == "user":
                self.chat_area.add_user_message(msg.content)
            else:
                card = self.chat_area.add_ai_message_with_card(msg.content)
                self._video_cards[msg.id] = card
                card.open_folder_clicked.connect(self._open_folder)
                if msg.status.value == "completed" and msg.local_path:
                    card.set_completed(msg.local_path)
                elif msg.status.value == "failed":
                    card.set_failed("生成失败")
                card.play_btn.clicked.connect(lambda _, p=msg.local_path: self._play_video(p))

    # ───────── 侧边栏事件 ─────────

    def _on_new_conversation(self) -> None:
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

    # ───────── 消息发送 ─────────

    def _on_message_sent(self, text: str) -> None:
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

        self.chat_area.add_user_message(text)
        self._service.add_user_message(self._current_conversation_id, text)

        try:
            assistant_msg = self._service.submit_task(
                self._current_conversation_id, text, provider_name
            )
        except Exception as e:
            logger.exception("提交任务失败")
            card = self.chat_area.add_ai_message_with_card(text)
            card.set_failed(str(e))
            return

        card = self.chat_area.add_ai_message_with_card("收到你的描述，正在生成视频…")
        card.open_folder_clicked.connect(self._open_folder)
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
            card.set_completed(local_path)
            card.play_btn.clicked.connect(lambda _, p=local_path: self._play_video(p))
        self._video_cards.pop(message_id, None)

    def _on_task_failed(self, message_id: str, error: str) -> None:
        card = self._video_cards.get(message_id)
        if card:
            card.set_failed(error)
        self._video_cards.pop(message_id, None)

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
            self._service._download_dir = self._config.settings.default_download_dir

    def closeEvent(self, event) -> None:
        self._service.shutdown()
        self._db.close()
        super().closeEvent(event)
