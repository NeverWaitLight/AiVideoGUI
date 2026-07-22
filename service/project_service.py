"""项目服务：管理项目 CRUD 和对话关联。"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime

from models.data_models import Conversation, Project
from storage.database import DatabaseManager

logger = logging.getLogger(__name__)


class ProjectService:
    """项目服务类。"""

    def __init__(self, db: DatabaseManager):
        self._db = db

    def create_project(self, name: str, resolution: str = "720P", aspect_ratio: str = "16:9", cover_image: str = "") -> Project:
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
        """删除项目（级联删除所有关联数据和文件）。"""
        logger.info(f"开始删除项目：project_id={project_id}")

        # 1. 查询项目关联的所有素材文件（通过对话关联）
        media_files = self._db.list_media_files(project_id=project_id)
        logger.info(f"找到 {len(media_files)} 个项目关联的素材文件")

        # 2. 删除素材文件（磁盘文件 + 缩略图 + 数据库记录）
        for media in media_files:
            # 删除视频/图片文件
            if media.local_path and os.path.exists(media.local_path):
                try:
                    os.remove(media.local_path)
                    logger.info(f"删除素材文件：{media.local_path}")
                except OSError as e:
                    logger.warning(f"删除素材文件失败 {media.local_path}: {e}")

            # 删除缩略图
            if media.thumbnail_path and os.path.exists(media.thumbnail_path):
                try:
                    os.remove(media.thumbnail_path)
                    logger.info(f"删除缩略图：{media.thumbnail_path}")
                except OSError as e:
                    logger.warning(f"删除缩略图失败 {media.thumbnail_path}: {e}")

            # 删除数据库记录
            self._db.delete_media_file(media.id)

        # 3. 数据库级联删除会自动处理：
        #    - outlines (ON DELETE CASCADE)
        #    - outline_history (ON DELETE CASCADE)
        #    - scripts (ON DELETE CASCADE)
        #    - scenes (ON DELETE CASCADE)
        #    - script_history (ON DELETE CASCADE)
        #    - shots (ON DELETE CASCADE)
        #    - shot_history (ON DELETE CASCADE)

        # 4. 删除项目（会清除对话的 project_id 关联）
        self._db.delete_project(project_id)

        logger.info(f"项目删除完成：project_id={project_id}")

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
