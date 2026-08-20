from __future__ import annotations

import os
import subprocess
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Property, Signal, Slot, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication

if TYPE_CHECKING:
    from di import ApplicationContainer

from bridge.project_bridge import ProjectBridge
from bridge.media_bridge import MediaBridge
from bridge.storyboard_bridge import StoryboardBridge
from bridge.story_outline_bridge import StoryOutlineBridge
from bridge.screenplay_bridge import ScreenplayBridge
from bridge.character_bridge import CharacterBridge
from bridge.settings_bridge import SettingsBridge
from bridge.visual_style_bridge import VisualStyleBridge
from bridge.update_bridge import UpdateBridge
from bridge.task_bridge import TaskBridge
from service.desktop_notification_service import DesktopNotificationService
from service.background.image_generation_worker import get_image_signal_emitter


class AppBridge(QObject):
    task_status_changed = Signal(str, str)
    task_download_progress = Signal(str, int, int)
    task_finished = Signal(str, str, int)
    task_failed = Signal(str, str)
    batch_progress = Signal(int, int, str)
    batch_done = Signal(int, int)
    batch_terminated = Signal(int, int)
    script_generated = Signal(str, list)
    script_failed = Signal(str)
    storyboard_generated = Signal(dict)
    storyboard_failed = Signal(str)
    design_image_ready = Signal(str, str)
    design_image_progress = Signal(str)
    design_image_failed = Signal(str)
    batch_design_progress = Signal(int, str, str)
    batch_design_done = Signal(int, int)
    navigate_requested = Signal(int, str, str)  # projectId, module, entityId
    close_choice_requested = Signal()
    cover_generation_started = Signal(int)
    cover_generation_finished = Signal(int, str)
    cover_generation_failed = Signal(int, str)

    def __init__(self, container, parent: QObject | None = None):
        super().__init__(parent)
        self._container = container
        self._video_service = container.video_service()
        self._project_service = container.project_service()
        self._story_outline_service = container.story_outline_service()
        self._screenplay_service = container.screenplay_service()
        self._storyboard_service = container.storyboard_service()
        self._character_service = container.character_service()
        self._text_model_service = container.chat_model_service()
        self._image_service = container.image_service()
        self._media_service = container.media_service()
        self._take_service = container.storyboard_take_service()
        self._session_manager = container.session_manager()
        self._config = container.config_manager()
        self._scheduler = container.background_scheduler()
        self._projects = ProjectBridge(
            self._project_service, self._session_manager,
            container.visual_style_service(),
            container.chat_model_service(),
            container.image_service(),
            container,
            self,
        )
        self._projects.set_workspace_root(container.config.workspace_root())
        self._projects.cover_generation_started.connect(self.cover_generation_started.emit)
        self._projects.cover_generation_finished.connect(self.cover_generation_finished.emit)
        self._projects.cover_generation_failed.connect(self.cover_generation_failed.emit)
        self._media = MediaBridge(
            self._media_service, self,
        )
        self._storyboard_bridge = StoryboardBridge(
            self._storyboard_service, self._screenplay_service,
            self._text_model_service, self._image_service,
            self._character_service, self._media_service,
            self._story_outline_service, self._project_service,
            container.visual_style_service(), self._container,
            take_service=self._take_service, parent=self,
        )
        self._story_outline = StoryOutlineBridge(
            self._story_outline_service, self._text_model_service,
            self._project_service, self,
        )
        self._screenplay = ScreenplayBridge(
            self._screenplay_service, self._text_model_service,
            self._story_outline_service, self._project_service, self,
        )
        self._characters = CharacterBridge(
            self._character_service, self._text_model_service,
            self._image_service, self._story_outline_service,
            self._screenplay_service, self._project_service,
            container.visual_style_service(), container, self,
        )
        self._settings_bridge = SettingsBridge(
            self._config, container.providers_catalog(), self
        )
        self._settings_bridge.settings_saved.connect(self._on_settings_saved)
        self._visual_styles = VisualStyleBridge(
            container.visual_style_service(), self,
        )
        self._update_bridge = UpdateBridge(container.update_service())
        self._task_bridge = TaskBridge(self._session_manager, self)
        self._video_polling_task = container.video_polling_task()
        signal_emitter = self._video_polling_task.signal_emitter
        signal_emitter.status_changed.connect(self.task_status_changed.emit)
        signal_emitter.download_progress.connect(self.task_download_progress.emit)
        signal_emitter.task_finished.connect(self.task_finished.emit)
        signal_emitter.task_finished.connect(self._on_video_task_finished)
        signal_emitter.task_failed.connect(self.task_failed.emit)
        self._storyboard_bridge.design_image_ready.connect(self.design_image_ready.emit)
        self._storyboard_bridge.design_image_progress.connect(self.design_image_progress.emit)
        self._storyboard_bridge.design_image_failed.connect(self.design_image_failed.emit)

        self._notifications = DesktopNotificationService(self._session_manager, self)
        self._notifications.navigate_requested.connect(self.navigate_requested.emit)
        self._notifications.restore_requested.connect(self.restore_window)
        self._notifications.quit_requested.connect(self.quit_application)
        signal_emitter.task_finished.connect(self._on_notify_video_finished)
        signal_emitter.task_failed.connect(self._on_notify_video_failed)
        image_emitter = get_image_signal_emitter()
        image_emitter.task_finished.connect(
            lambda pid, _ct, _cid, _path: self._on_notify_image_finished(pid)
        )
        image_emitter.task_failed.connect(
            lambda pid, _ct, _cid, err: self._on_notify_image_failed(pid, err)
        )

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
    def visualStyles(self):
        return self._visual_styles

    @Property(QObject, constant=True)
    def update(self):
        return self._update_bridge

    @Property(QObject, constant=True)
    def tasks(self):
        return self._task_bridge

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

    def _window(self):
        windows = QGuiApplication.topLevelWindows()
        return windows[0] if windows else None

    @Slot()
    def minimize_window(self) -> None:
        w = self._window()
        if w:
            w.showMinimized()

    @Slot()
    def toggle_maximize(self) -> None:
        w = self._window()
        if w:
            if w.windowStates() & Qt.WindowMaximized:
                w.showNormal()
            else:
                w.showMaximized()

    @Slot()
    def close_window(self) -> None:
        action = self._config.settings.close_window_action or ""
        if action == "minimize":
            self.hide_to_tray()
        elif action == "quit":
            self.quit_application()
        else:
            self.close_choice_requested.emit()

    @Slot()
    def hide_to_tray(self) -> None:
        w = self._window()
        if w:
            w.hide()

    @Slot()
    def restore_window(self) -> None:
        w = self._window()
        if not w:
            return
        if w.windowStates() & Qt.WindowMinimized:
            w.showNormal()
        else:
            w.show()
        w.raise_()
        w.requestActivate()

    @Slot()
    def quit_application(self) -> None:
        QApplication.quit()

    def _on_video_task_finished(self, provider_task_id: str, save_path: str, storyboard_id: int) -> None:
        self._media.files_changed.emit()
        if storyboard_id > 0:
            try:
                media = self._media_service.get_file_by_message_id(provider_task_id)
                if media:
                    self._take_service.bind_media_by_provider_task_id(
                        provider_task_id=provider_task_id,
                        media_file_id=media.id,
                    )
                    self._storyboard_bridge.takes_changed.emit()
            except Exception as e:
                from loguru import logger
                logger.warning(f"回填拍摄记录媒体失败: {e}")

    def _on_notify_video_finished(self, provider_task_id: str, save_path: str, storyboard_id: int) -> None:
        self._notifications.notify_generate_task(provider_task_id, True)

    def _on_notify_video_failed(self, provider_task_id: str, error: str) -> None:
        self._notifications.notify_generate_task(provider_task_id, False, error)

    def _on_notify_image_finished(self, provider_task_id: str) -> None:
        self._notifications.notify_generate_task(provider_task_id, True)

    def _on_notify_image_failed(self, provider_task_id: str, error: str) -> None:
        self._notifications.notify_generate_task(provider_task_id, False, error)

    def _on_settings_saved(self) -> None:
        self._text_model_service.invalidate_provider_cache()
        self._video_service.invalidate_provider_cache()
        self._image_service.invalidate_provider_cache()
        self._video_polling_task.invalidate_provider_cache()

