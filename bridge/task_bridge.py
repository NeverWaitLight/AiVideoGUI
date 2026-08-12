from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Slot
from loguru import logger

if TYPE_CHECKING:
    from storage.session_manager import SessionManager

from storage.repositories.generate_task_repository import GenerateTaskRepository


class TaskBridge(QObject):
    def __init__(self, session_manager: SessionManager, parent: QObject | None = None):
        super().__init__(parent)
        self._session_manager = session_manager

    @Slot(result=list)
    def list_all_tasks(self) -> list:
        try:
            repo = self._session_manager.get_repo(GenerateTaskRepository)
            active = repo.list_active_tasks()
            completed = repo.list_completed_tasks(limit=100)
            all_tasks = active + completed
            all_tasks.sort(key=lambda x: x["created_at"], reverse=True)
            return all_tasks
        except Exception as e:
            logger.error(f"获取任务列表失败: {e}")
            return []

    @Slot(int, result="QVariantMap")
    def get_task_detail(self, task_id: int) -> dict:
        try:
            repo = self._session_manager.get_repo(GenerateTaskRepository)
            task = repo.get_by_id(task_id)
            return task if task else {}
        except Exception as e:
            logger.error(f"获取任务详情失败: {e}")
            return {}

    @Slot(int, str, result=list)
    def list_tasks_filtered(self, project_id: int, caller_type: str) -> list:
        try:
            repo = self._session_manager.get_repo(GenerateTaskRepository)

            pid = None if project_id == -1 else project_id
            ctype = None if caller_type == "" else caller_type

            tasks = repo.list_tasks_with_filters(
                project_id=pid,
                caller_type=ctype,
                limit=150
            )

            return tasks
        except Exception as e:
            logger.error(f"获取过滤任务列表失败: {e}")
            return []
