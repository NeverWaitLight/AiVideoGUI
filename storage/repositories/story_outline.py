"""故事大纲 Repository。"""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.story_outline import StoryOutline, StoryOutlineHistory
from storage.orm.models import StoryOutlineEntity, StoryOutlineHistoryEntity
from storage.repositories.base import BaseRepository


class StoryOutlineRepository(BaseRepository[StoryOutlineEntity, StoryOutline]):
    """故事大纲 Repository。"""

    def __init__(self, session: Session):
        super().__init__(session, StoryOutlineEntity)

    def _to_dto(self, entity: StoryOutlineEntity) -> StoryOutline:
        """Entity → DTO 转换。"""
        return StoryOutline(
            id=entity.id if entity.id is not None else 0,
            project_id=entity.project_id,
            content=entity.content,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def _to_entity(self, dto: StoryOutline) -> StoryOutlineEntity:
        """DTO → Entity 转换。"""
        entity = StoryOutlineEntity(
            project_id=dto.project_id,
            content=dto.content,
            created_at=dto.created_at,
            updated_at=dto.updated_at,
        )
        return entity

    def get_by_project(self, project_id: int) -> Optional[StoryOutline]:
        """
        查询项目的故事大纲。

        Args:
            project_id: 项目 ID

        Returns:
            大纲对象，如果不存在则返回 None
        """
        stmt = select(StoryOutlineEntity).where(StoryOutlineEntity.project_id == project_id)
        entity = self.session.execute(stmt).scalars().first()
        return self._to_dto(entity) if entity else None

    def update_content(self, story_outline_id: int, content: str, updated_at: int) -> None:
        """
        更新故事大纲内容。

        Args:
            story_outline_id: 大纲 ID
            content: 新内容
            updated_at: 更新时间（13位时间戳毫秒）
        """
        entity = self.session.get(StoryOutlineEntity, story_outline_id)
        if not entity:
            return

        entity.content = content
        entity.updated_at = updated_at
        self.session.commit()


class StoryOutlineHistoryRepository(BaseRepository[StoryOutlineHistoryEntity, StoryOutlineHistory]):
    """故事大纲历史 Repository。"""

    def __init__(self, session: Session):
        super().__init__(session, StoryOutlineHistoryEntity)

    def _to_dto(self, entity: StoryOutlineHistoryEntity) -> StoryOutlineHistory:
        """Entity → DTO 转换。"""
        return StoryOutlineHistory(
            id=entity.id if entity.id is not None else 0,
            story_outline_id=entity.story_outline_id,
            project_id=entity.project_id,
            content=entity.content,
            created_at=entity.created_at,
        )

    def _to_entity(self, dto: StoryOutlineHistory) -> StoryOutlineHistoryEntity:
        """DTO → Entity 转换。"""
        return StoryOutlineHistoryEntity(
            id=dto.id,
            story_outline_id=dto.story_outline_id,
            project_id=dto.project_id,
            content=dto.content,
            created_at=dto.created_at,
        )

    def list_by_story_outline(self, story_outline_id: int) -> List[StoryOutlineHistory]:
        """
        查询故事大纲的所有历史版本（按时间倒序）。

        Args:
            story_outline_id: 大纲 ID

        Returns:
            历史版本列表
        """
        stmt = (
            select(StoryOutlineHistoryEntity)
            .where(StoryOutlineHistoryEntity.story_outline_id == story_outline_id)
            .order_by(StoryOutlineHistoryEntity.created_at.desc())
        )
        entities = self.session.execute(stmt).scalars().all()
        return [self._to_dto(e) for e in entities]
