from loguru import logger
import time

from models.story_outline import StoryOutline, StoryOutlineHistory
from storage.session_manager import SessionManager
from storage.repositories.story_outline_repository import StoryOutlineRepository, StoryOutlineHistoryRepository

class StoryOutlineService:

    def __init__(self, session_manager: SessionManager) -> None:
        self._sm = session_manager

    def get_or_create_story_outline(self, project_id: int) -> StoryOutline:
        outline_repo = self._sm.get_repo(StoryOutlineRepository)

        story_outline = outline_repo.get_by_project(project_id)
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

        self._sm.begin_write()
        try:
            created = outline_repo.create(story_outline)
            self._sm.commit_write()
            logger.info(f"为项目 {project_id} 创建新故事大纲，ID: {created.id}")
            return created
        except Exception as e:
            self._sm.rollback_write()
            logger.error(f"创建故事大纲失败：{e}")
            raise

    def update_story_outline(self, story_outline_id: int, content: str) -> None:
        outline_repo = self._sm.get_repo(StoryOutlineRepository)
        now_ms = int(time.time() * 1000)

        self._sm.begin_write()
        try:
            outline_repo.update_content(story_outline_id, content, now_ms)
            self._sm.commit_write()
            logger.info(f"更新故事大纲 {story_outline_id}")
        except Exception as e:
            self._sm.rollback_write()
            logger.error(f"更新故事大纲失败：{e}")
            raise

    def list_history(self, story_outline_id: int) -> list[StoryOutlineHistory]:
        history_repo = self._sm.get_repo(StoryOutlineHistoryRepository)
        return history_repo.list_by_story_outline(story_outline_id)

    def restore_from_history(self, story_outline_id: int, history_id: int) -> None:
        outline_repo = self._sm.get_repo(StoryOutlineRepository)
        history_repo = self._sm.get_repo(StoryOutlineHistoryRepository)

        self._sm.begin_write()
        try:
            history = history_repo.get_by_id(history_id)
            if not history:
                raise ValueError(f"历史版本不存在：{history_id}")

            now_ms = int(time.time() * 1000)
            outline_repo.update_content(story_outline_id, history.content, now_ms)

            self._sm.commit_write()
            logger.info(f"从历史版本 {history_id} 恢复故事大纲 {story_outline_id}")
        except Exception as e:
            self._sm.rollback_write()
            logger.error(f"恢复故事大纲失败：{e}")
            raise
