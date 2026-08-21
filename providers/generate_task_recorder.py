from __future__ import annotations

import json
import uuid
from typing import Any

from models.enums import GenerateTaskCallerType, GenerateTaskType
from storage.repositories.generate_task_repository import GenerateTaskRepository
from storage.session_manager import SessionManager
from utils.paths import workspace_root
from utils.response_data import normalize_response_data


class GenerateTaskRecorder:
    def __init__(self, session_manager: SessionManager) -> None:
        self._sm = session_manager

    def _normalize_response(
        self,
        task_id: int,
        response_data: Any = None,
        content_type: str = "",
    ) -> str:
        if response_data is None or response_data == "":
            return ""
        return normalize_response_data(
            response_data,
            workspace_root=workspace_root(),
            task_id=task_id,
            content_type=content_type,
        )

    def create_pending(
        self,
        *,
        provider_name: str,
        model_name: str,
        request_params: str | dict[str, Any],
        task_type: GenerateTaskType,
        local_path: str = "",
        caller_type: GenerateTaskCallerType | None = None,
        caller_id: str = "",
        project_id: int | None = None,
        parent_ids: str = "",
        provider_task_id: str | None = None,
    ) -> tuple[str, int]:
        if isinstance(request_params, dict):
            request_params_str = json.dumps(request_params, ensure_ascii=False)
        else:
            request_params_str = request_params

        pending_provider_task_id = provider_task_id or str(uuid.uuid4())
        task_repo = self._sm.get_repo(repo_class=GenerateTaskRepository)
        self._sm.begin_write()
        try:
            task_id = task_repo.add(
                provider_task_id=pending_provider_task_id,
                provider_name=provider_name,
                model_name=model_name,
                local_path=local_path,
                request_params=request_params_str,
                type=task_type,
                caller_type=caller_type,
                caller_id=caller_id,
                project_id=project_id,
                parent_ids=parent_ids,
            )
            self._sm.commit_write()
        except Exception:
            self._sm.rollback_write()
            raise
        return pending_provider_task_id, task_id

    def update_provider_task_id(
        self,
        task_id: int,
        provider_task_id: str,
        request_params: str | dict[str, Any] | None = None,
    ) -> None:
        if isinstance(request_params, dict):
            request_params_str = json.dumps(request_params, ensure_ascii=False)
        elif request_params is None:
            request_params_str = ""
        else:
            request_params_str = request_params

        task_repo = self._sm.get_repo(repo_class=GenerateTaskRepository)
        self._sm.begin_write()
        try:
            task_repo.update_provider_task_id(
                task_id,
                provider_task_id,
                request_params=request_params_str,
            )
            self._sm.commit_write()
        except Exception:
            self._sm.rollback_write()
            raise

    def mark_succeeded(
        self,
        task_id: int,
        remote_url: str = "",
        response_data: Any = None,
        content_type: str = "",
    ) -> None:
        normalized = self._normalize_response(task_id, response_data, content_type)
        task_repo = self._sm.get_repo(repo_class=GenerateTaskRepository)
        self._sm.begin_write()
        try:
            task_repo.update_status(
                task_id,
                "succeeded",
                remote_url=remote_url,
                response_data=normalized,
            )
            task_repo.mark_completed(task_id)
            self._sm.commit_write()
        except Exception:
            self._sm.rollback_write()
            raise

    def mark_failed(self, task_id: int, error_message: str) -> None:
        task_repo = self._sm.get_repo(repo_class=GenerateTaskRepository)
        self._sm.begin_write()
        try:
            task_repo.update_status(task_id, "failed", error_message=error_message)
            task_repo.mark_completed(task_id)
            self._sm.commit_write()
        except Exception:
            self._sm.rollback_write()
            raise

    def update_status(
        self,
        task_id: int,
        status: str,
        remote_url: str = "",
        error_message: str = "",
        response_data: Any = None,
        content_type: str = "",
    ) -> None:
        normalized = self._normalize_response(task_id, response_data, content_type)
        task_repo = self._sm.get_repo(repo_class=GenerateTaskRepository)
        self._sm.begin_write()
        try:
            task_repo.update_status(
                task_id,
                status,
                remote_url=remote_url,
                error_message=error_message,
                response_data=normalized,
            )
            self._sm.commit_write()
        except Exception:
            self._sm.rollback_write()
            raise
