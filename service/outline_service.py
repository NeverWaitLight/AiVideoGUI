"""大纲服务层：管理项目大纲的创建、更新和历史版本。"""

import logging
import time

from models.data_models import Outline, OutlineHistory
from storage.database import DatabaseManager

logger = logging.getLogger(__name__)


class OutlineService:
    """大纲服务：管理项目大纲。"""

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    def get_or_create_outline(self, project_id: int) -> Outline:
        """获取或创建项目大纲（每个项目只有一个大纲）。"""
        outline = self._db.get_outline(project_id)
        if outline:
            return outline

        # 创建新大纲
        now_ms = int(time.time() * 1000)
        outline = Outline(
            id=0,  # 自增ID，数据库自动生成
            project_id=project_id,
            content="",
            created_at=now_ms,
            updated_at=now_ms,
        )
        created_outline = self._db.create_outline(outline)
        logger.info(f"为项目 {project_id} 创建新大纲，ID: {created_outline.id}")
        return created_outline

    def update_outline(self, outline_id: int, content: str) -> None:
        """更新大纲内容（自动保存历史版本）。"""
        self._db.update_outline(outline_id, content)
        logger.info(f"更新大纲 {outline_id}")

    def list_history(self, outline_id: int) -> list[OutlineHistory]:
        """获取大纲的历史版本列表。"""
        return self._db.list_outline_history(outline_id)

    def restore_from_history(self, outline_id: int, history_id: int) -> None:
        """从历史版本恢复大纲。"""
        self._db.restore_outline_from_history(outline_id, history_id)
        logger.info(f"从历史版本 {history_id} 恢复大纲 {outline_id}")
