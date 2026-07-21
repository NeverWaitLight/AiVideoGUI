"""项目服务：管理项目 CRUD 和对话关联。"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime

from models.data_models import Conversation, Project
from storage.database import DatabaseManager

logger = logging.getLogger(__name__)


class ProjectService:
    """项目服务类。"""

    def __init__(self, db: DatabaseManager):
        self._db = db

    def create_project(self, name: str, resolution: str = "1280x720", aspect_ratio: str = "16:9", cover_image: str = "") -> Project:
        """创建新项目。"""
        project_id = str(uuid.uuid4())
        self._db.create_project(project_id, name, resolution, aspect_ratio, cover_image)
        return Project(
            id=project_id,
            name=name,
            resolution=resolution,
            aspect_ratio=aspect_ratio,
            created_at=datetime.now(),
            cover_image=cover_image,
        )

    def list_projects(self) -> list[Project]:
        """列出所有项目。"""
        rows = self._db.list_projects()
        return [
            Project(
                id=r["id"],
                name=r["name"],
                resolution=r["resolution"],
                aspect_ratio=r["aspect_ratio"],
                created_at=datetime.fromisoformat(r["created_at"]),
                cover_image=r.get("cover_image", ""),
            )
            for r in rows
        ]

    def get_project(self, project_id: str) -> Project | None:
        """获取单个项目。"""
        row = self._db.get_project(project_id)
        if not row:
            return None
        return Project(
            id=row["id"],
            name=row["name"],
            resolution=row["resolution"],
            aspect_ratio=row["aspect_ratio"],
            created_at=datetime.fromisoformat(row["created_at"]),
            cover_image=row.get("cover_image", ""),
        )

    def update_project(self, project_id: str, name: str, resolution: str, aspect_ratio: str, cover_image: str = "") -> None:
        """更新项目信息。"""
        self._db.update_project(project_id, name, resolution, aspect_ratio, cover_image)

    def delete_project(self, project_id: str) -> None:
        """删除项目（会清除关联对话的 project_id）。"""
        self._db.delete_project(project_id)

    def list_project_conversations(self, project_id: str) -> list[Conversation]:
        """列出项目下的所有对话。"""
        return self._db.list_project_conversations(project_id)

    def get_project_video_count(self, project_id: str) -> int:
        """获取项目下的视频总数。"""
        convs = self._db.list_project_conversations(project_id)
        count = 0
        for conv in convs:
            messages = self._db.list_messages(conv.id)
            count += sum(1 for msg in messages if msg.role == "assistant" and msg.local_path)
        return count
