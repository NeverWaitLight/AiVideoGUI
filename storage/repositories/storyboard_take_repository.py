from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.enums import TakeStatus
from models.storyboard_take import StoryboardTake
from storage.orm.storyboard_take_entity import StoryboardTakeEntity
from storage.repositories.base_repository import BaseRepository


class StoryboardTakeRepository(BaseRepository[StoryboardTakeEntity, StoryboardTake]):

    def __init__(self, session: Session, workspace_root: str = ""):
        super().__init__(session, StoryboardTakeEntity)
        self._workspace_root = workspace_root

    def _to_dto(self, entity: StoryboardTakeEntity) -> StoryboardTake:
        return StoryboardTake(
            id=entity.id,
            storyboard_id=entity.storyboard_id,
            number=entity.number,
            media_file_id=entity.media_file_id,
            status=TakeStatus(entity.status) if isinstance(entity.status, str) else entity.status,
            comment=entity.comment,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def _to_entity(self, dto: StoryboardTake) -> StoryboardTakeEntity:
        entity = StoryboardTakeEntity(
            storyboard_id=dto.storyboard_id,
            number=dto.number,
            media_file_id=dto.media_file_id,
            status=dto.status.value if isinstance(dto.status, TakeStatus) else dto.status,
            comment=dto.comment,
            created_at=dto.created_at,
            updated_at=dto.updated_at,
        )
        if dto.id > 0:
            entity.id = dto.id
        return entity

    def list_by_storyboard(self, storyboard_id: int) -> List[StoryboardTake]:
        stmt = (
            select(StoryboardTakeEntity)
            .where(StoryboardTakeEntity.storyboard_id == storyboard_id)
            .order_by(StoryboardTakeEntity.number.asc())
        )
        entities = self.session.execute(stmt).scalars().all()
        return [self._to_dto(e) for e in entities]

    def get_next_number(self, storyboard_id: int) -> int:
        stmt = (
            select(func.max(StoryboardTakeEntity.number))
            .where(StoryboardTakeEntity.storyboard_id == storyboard_id)
        )
        max_number = self.session.execute(stmt).scalar_one_or_none()
        return (max_number or 0) + 1

    def list_selected_by_project(self, project_id: int) -> List[StoryboardTake]:
        from storage.orm.storyboard_entity import StoryboardEntity
        from storage.orm.screenplay_entity import ScreenplayEntity

        stmt = (
            select(StoryboardTakeEntity)
            .join(StoryboardEntity, StoryboardTakeEntity.storyboard_id == StoryboardEntity.id)
            .join(ScreenplayEntity, StoryboardEntity.scene_id == ScreenplayEntity.id)
            .where(
                ScreenplayEntity.project_id == project_id,
                StoryboardTakeEntity.status == TakeStatus.SELECTED.value,
            )
            .order_by(StoryboardEntity.scene_number, StoryboardEntity.shot_number, StoryboardTakeEntity.number)
        )
        entities = self.session.execute(stmt).scalars().all()
        return [self._to_dto(e) for e in entities]
