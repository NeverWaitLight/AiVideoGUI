"""故事大纲服务层：管理项目大纲的创建、更新和历史版本。"""

from loguru import logger
import time

from models.story_outline import StoryOutline, StoryOutlineHistory
from storage.database import DatabaseManager

class StoryOutlineService:
    """故事大纲服务：管理项目大纲。"""

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    def get_or_create_story_outline(self, project_id: int) -> StoryOutline:
        """获取或创建项目故事大纲（每个项目只有一个大纲）。"""
        story_outline = self._db.get_story_outline(project_id)
        if story_outline:
            return story_outline

        now_ms = int(time.time() * 1000)
        story_outline = StoryOutline(
            id=0,
            project_id=project_id,
            content="",
            created_at=now_ms,
            updated_at=now_ms,
        )
        created = self._db.create_story_outline(story_outline)
        logger.info(f"为项目 {project_id} 创建新故事大纲，ID: {created.id}")
        return created

    def update_story_outline(self, story_outline_id: int, content: str) -> None:
        """更新故事大纲内容（自动保存历史版本）。"""
        self._db.update_story_outline(story_outline_id, content)
        logger.info(f"更新故事大纲 {story_outline_id}")

    def list_history(self, story_outline_id: int) -> list[StoryOutlineHistory]:
        """获取故事大纲的历史版本列表。"""
        return self._db.list_story_outline_history(story_outline_id)

    def restore_from_history(self, story_outline_id: int, history_id: int) -> None:
        """从历史版本恢复故事大纲。"""
        self._db.restore_story_outline_from_history(story_outline_id, history_id)
        logger.info(f"从历史版本 {history_id} 恢复故事大纲 {story_outline_id}")
