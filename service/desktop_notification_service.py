"""Windows 桌面通知：视频/图片生成任务完成或失败时弹出系统通知。"""
from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger
from PySide6.QtCore import QObject, Qt, Signal, Slot
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtWidgets import QSystemTrayIcon

if TYPE_CHECKING:
    from storage.session_manager import SessionManager

_CALLER_TO_MODULE: dict[str, str] = {
    "storyboard": "storyboard",
    "character": "character",
    "cover": "project_info",
    "outline": "outline",
    "script": "screenplay",
}

_TYPE_LABELS: dict[str, str] = {
    "video": "视频",
    "image": "图片",
}


class DesktopNotificationService(QObject):
    navigate_requested = Signal(int, str, str)  # project_id, module, entity_id
    _notify_requested = Signal(str, bool, str)  # provider_task_id, success, error

    def __init__(self, session_manager: SessionManager, parent: QObject | None = None):
        super().__init__(parent)
        self._session_manager = session_manager
        self._pending_nav: tuple[int, str, str] | None = None

        self._tray = QSystemTrayIcon(self)
        self._tray.setIcon(QIcon(":/resources/logo.ico"))
        self._tray.setToolTip("AI Video GUI")
        self._tray.messageClicked.connect(self._on_message_clicked)
        self._tray.show()

        self._notify_requested.connect(self._notify_on_main_thread, Qt.ConnectionType.QueuedConnection)

    def notify_generate_task(self, provider_task_id: str, success: bool, error: str = "") -> None:
        """根据 provider_task_id 弹出通知。可从任意线程调用（会排队到主线程）。"""
        self._notify_requested.emit(provider_task_id, success, error or "")

    @Slot(str, bool, str)
    def _notify_on_main_thread(self, provider_task_id: str, success: bool, error: str) -> None:
        try:
            from storage.repositories.generate_task_repository import GenerateTaskRepository

            repo = self._session_manager.get_repo(GenerateTaskRepository)
            task = repo.get_by_provider_task_id(provider_task_id)
            if not task:
                logger.warning(f"通知跳过：任务不存在 provider_task_id={provider_task_id}")
                return

            task_type = (task.get("type") or "").lower()
            if task_type not in ("video", "image"):
                return

            label = _TYPE_LABELS.get(task_type, "任务")
            title = f"{label}生成完成" if success else f"{label}生成失败"
            caller_type = task.get("caller_type") or ""
            caller_labels = {
                "storyboard": "分镜",
                "character": "角色",
                "cover": "封面",
                "outline": "大纲",
                "script": "剧本",
            }
            caller_label = caller_labels.get(caller_type, "")
            if success:
                body = f"{caller_label}{label}已就绪，点击查看" if caller_label else "点击查看结果"
            else:
                err = (error or task.get("error_message") or "未知错误").strip()
                if len(err) > 120:
                    err = err[:117] + "..."
                body = err

            module = _CALLER_TO_MODULE.get(caller_type, "detail")
            project_id = int(task.get("project_id") or -1)
            entity_id = str(task.get("caller_id") or "")

            self._pending_nav = (project_id, module, entity_id)

            icon = (
                QSystemTrayIcon.MessageIcon.Information
                if success
                else QSystemTrayIcon.MessageIcon.Warning
            )
            self._tray.showMessage(title, body, icon, 8000)
            logger.info(f"已弹出系统通知：{title} provider_task_id={provider_task_id}")
        except Exception as e:
            logger.warning(f"弹出系统通知失败：{e}")

    def _on_message_clicked(self) -> None:
        self._activate_window()
        if self._pending_nav is None:
            return
        project_id, module, entity_id = self._pending_nav
        if project_id <= 0:
            return
        self.navigate_requested.emit(project_id, module, entity_id)

    def _activate_window(self) -> None:
        windows = QGuiApplication.topLevelWindows()
        if not windows:
            return
        w = windows[0]
        if w.windowStates() & Qt.WindowState.WindowMinimized:
            w.showNormal()
        else:
            w.show()
        w.raise_()
        w.requestActivate()
