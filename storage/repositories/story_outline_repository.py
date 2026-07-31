from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.story_outline import StoryOutline, StoryOutlineHistory
from storage.orm.story_outline_entity import StoryOutlineEntity, StoryOutlineHistoryEntity
from storage.repositories.base_repository import BaseRepository


class StoryOutlineRepository(BaseRepository[StoryOutlineEntity, StoryOutline]):

    def __init__(self, session: Session):
        super().__init__(session, StoryOutlineEntity)

    def _to_dto(self, entity: StoryOutlineEntity) -> StoryOutline:
        return StoryOutline(
            id=entity.id if entity.id is not None else 0,
            project_id=entity.project_id,
            content=entity.content,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def _to_entity(self, dto: StoryOutline) -> StoryOutlineEntity:
        entity = StoryOutlineEntity(
            project_id=dto.project_id,
            content=dto.content,
            created_at=dto.created_at,
            updated_at=dto.updated_at,
        )
        return entity

    def get_by_project(self, project_id: int) -> Optional[StoryOutline]:
        stmt = select(StoryOutlineEntity).where(StoryOutlineEntity.project_id == project_id)
        entity = self.session.execute(stmt).scalars().first()
        return self._to_dto(entity) if entity else None

    def update_content(self, story_outline_id: int, content: str, updated_at: int) -> None:
        entity = self.session.get(StoryOutlineEntity, story_outline_id)
        if not entity:
            return

        entity.content = content
        entity.updated_at = updated_at
        self.session.commit()


class StoryOutlineHistoryRepository(BaseRepository[StoryOutlineHistoryEntity, StoryOutlineHistory]):

    def __init__(self, session: Session):
        super().__init__(session, StoryOutlineHistoryEntity)

    def _to_dto(self, entity: StoryOutlineHistoryEntity) -> StoryOutlineHistory:
        return StoryOutlineHistory(
            id=entity.id if entity.id is not None else 0,
            story_outline_id=entity.story_outline_id,
            project_id=entity.project_id,
            content=entity.content,
            created_at=entity.created_at,
        )

    def _to_entity(self, dto: StoryOutlineHistory) -> StoryOutlineHistoryEntity:
        return StoryOutlineHistoryEntity(
            id=dto.id,
            story_outline_id=dto.story_outline_id,
            project_id=dto.project_id,
            content=dto.content,
            created_at=dto.created_at,
        )

    def list_by_story_outline(self, story_outline_id: int) -> List[StoryOutlineHistory]:
        stmt = (
            select(StoryOutlineHistoryEntity)
            .where(StoryOutlineHistoryEntity.story_outline_id == story_outline_id)
            .order_by(StoryOutlineHistoryEntity.created_at.desc())
        )
        entities = self.session.execute(stmt).scalars().all()
        return [self._to_dto(e) for e in entities]
