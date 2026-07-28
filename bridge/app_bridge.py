"""Python ↔ QML 统一桥接入口。通过 setContextProperty 暴露给 QML。"""

from __future__ import annotations

import os
import subprocess
from loguru import logger
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Property, Signal, Slot

if TYPE_CHECKING:
    from di import ApplicationContainer

from bridge.conversation_bridge import ConversationBridge
from bridge.project_bridge import ProjectBridge
from bridge.media_bridge import MediaBridge
from bridge.storyboard_bridge import StoryboardBridge
from bridge.story_outline_bridge import StoryOutlineBridge
from bridge.screenplay_bridge import ScreenplayBridge
from bridge.character_bridge import CharacterBridge
from bridge.settings_bridge import SettingsBridge
from bridge.video_player_bridge import VideoPlayerBridge


class AppBridge(QObject):
    """QML 前端的唯一 Python 入口。"""

    # ── 轮询服务信号转发 ──
    task_status_changed = Signal(str, str)
    task_download_progress = Signal(str, int, int)
    task_finished = Signal(str, str, int)
    task_failed = Signal(str, str)

    # ── 对话服务信号转发 ──
    title_ready = Signal(str, str)

    # ── 批量生成信号 ──
    batch_progress = Signal(int, int, str)
    batch_done = Signal(int, int)
    batch_terminated = Signal(int, int)

    # ── AI Worker 信号 ──
    script_generated = Signal(str, list)
    script_failed = Signal(str)
    storyboard_generated = Signal(dict)
    storyboard_failed = Signal(str)
    design_image_ready = Signal(str, str)
    design_image_progress = Signal(str)
    design_image_failed = Signal(str)
    batch_design_progress = Signal(int, str, str)
    batch_design_done = Signal(int, int)

    # ── 导航 ──
    navigate_requested = Signal(str, str)  # page_name, params_json

    def __init__(self, container, parent: QObject | None = None):
        super().__init__(parent)
        self._container = container

        # Service 实例
        self._video_service = container.video_service()
        self._chat_service = container.chat_service()
        self._project_service = container.project_service()
        self._story_outline_service = container.story_outline_service()
        self._screenplay_service = container.screenplay_service()
        self._storyboard_service = container.storyboard_service()
        self._character_service = container.character_service()
        self._text_model_service = container.text_model_service()
        self._image_service = container.image_service()
        self._media_service = container.media_service()
        self._polling_service = container.task_polling_service()
        self._session_manager = container.session_manager()
        self._config = container.config_manager()

        # 子 Bridge
        self._conversations = ConversationBridge(
            self._video_service, self._chat_service, self._session_manager, self,
        )
        self._projects = ProjectBridge(
            self._project_service, self._session_manager, self,
        )
        self._media = MediaBridge(
            self._media_service, self,
        )
        self._storyboard_bridge = StoryboardBridge(
            self._storyboard_service, self._screenplay_service,
            self._text_model_service, self._image_service,
            self._character_service, self._media_service,
            self._container, self,
        )
        self._story_outline = StoryOutlineBridge(
            self._story_outline_service, self._text_model_service, self,
        )
        self._screenplay = ScreenplayBridge(
            self._screenplay_service, self._text_model_service, self,
        )
        self._characters = CharacterBridge(
            self._character_service, self._text_model_service,
            self._image_service, self,
        )
        self._settings_bridge = SettingsBridge(self._config, self)
        self._video_player = VideoPlayerBridge(self._session_manager, self)

        # 转发轮询服务信号
        self._polling_service.status_changed.connect(self.task_status_changed.emit)
        self._polling_service.download_progress.connect(self.task_download_progress.emit)
        self._polling_service.task_finished.connect(self.task_finished.emit)
        self._polling_service.task_failed.connect(self.task_failed.emit)

        # 转发对话服务信号
        self._chat_service.title_ready.connect(self.title_ready.emit)

        # 转发分镜 Bridge 信号
        self._storyboard_bridge.design_image_ready.connect(self.design_image_ready.emit)
        self._storyboard_bridge.design_image_progress.connect(self.design_image_progress.emit)
        self._storyboard_bridge.design_image_failed.connect(self.design_image_failed.emit)

        # 启动轮询服务
        self._polling_service.start()

    # ── 子 Bridge 属性 ──

    @Property(QObject, constant=True)
    def conversations(self):
        return self._conversations

    @Property(QObject, constant=True)
    def projects(self):
        return self._projects

    @Property(QObject, constant=True)
    def media(self):
        return self._media

    @Property(QObject, constant=True)
    def storyboard(self):
        return self._storyboard_bridge

    @Property(QObject, constant=True)
    def storyOutline(self):
        return self._story_outline

    @Property(QObject, constant=True)
    def screenplay(self):
        return self._screenplay

    @Property(QObject, constant=True)
    def characters(self):
        return self._characters

    @Property(QObject, constant=True)
    def settings(self):
        return self._settings_bridge

    @Property(QObject, constant=True)
    def videoPlayer(self):
        return self._video_player

    # ── 全局操作 ──

    @Slot(str)
    def play_video(self, path: str) -> None:
        if os.path.isfile(path):
            os.startfile(path)

    @Slot(str)
    def open_folder(self, path: str) -> None:
        if os.path.isfile(path):
            subprocess.run(["explorer", "/select,", path])
        elif os.path.isdir(path):
            os.startfile(path)

    @Slot(str, str)
    def show_in_explorer(self, path: str, select: str = "") -> None:
        target = select if select else path
        if os.path.exists(target):
            subprocess.run(["explorer", "/select,", target])
