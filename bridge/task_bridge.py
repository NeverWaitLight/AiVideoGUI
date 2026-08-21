from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QObject, Slot
from loguru import logger

if TYPE_CHECKING:
    from storage.session_manager import SessionManager

from storage.repositories.generate_task_repository import GenerateTaskRepository


def _resolve_display_local_path(parent_info: dict[str, Any] | None, task: dict[str, Any]) -> str:
    if parent_info:
        local_path = parent_info.get("local_path", "") or ""
        if not local_path:
            try:
                params = json.loads(parent_info.get("request_params", "{}") or "{}")
                local_path = params.get("local_path", "") or ""
            except (json.JSONDecodeError, TypeError):
                local_path = ""
        if local_path:
            return local_path
    return task.get("local_path", "") or ""


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
            if not task:
                return {}

            if not (task.get("local_path") or "").strip():
                parent_id = GenerateTaskRepository.get_parent_task_id(task.get("parent_ids", ""))
                parent_info = repo.get_by_id(parent_id) if parent_id else None
                resolved = _resolve_display_local_path(parent_info, task)
                if resolved:
                    task = dict(task)
                    task["local_path"] = resolved

            return task
        except Exception as e:
            logger.error(f"获取任务详情失败: {e}")
            return {}

    @Slot(int, result=list)
    def list_child_tasks(self, parent_id: int) -> list:
        try:
            repo = self._session_manager.get_repo(GenerateTaskRepository)
            return repo.list_child_tasks_by_parent_id(parent_id)
        except Exception as e:
            logger.error(f"获取子任务列表失败: {e}")
            return []

    @Slot(int, str, result=list)
    def list_tasks_filtered(self, project_id: int, task_type: str) -> list:
        try:
            repo = self._session_manager.get_repo(GenerateTaskRepository)

            pid = None if project_id == -1 else project_id
            ttype = None if task_type == "" else task_type

            tasks = repo.list_tasks_with_filters(
                project_id=pid,
                task_type=ttype,
                limit=150
            )

            return tasks
        except Exception as e:
            logger.error(f"获取过滤任务列表失败: {e}")
            return []
