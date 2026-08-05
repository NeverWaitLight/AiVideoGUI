from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from models.visual_style import VisualStyle
from storage.orm.visual_style_entity import VisualStyleEntity
from storage.repositories.base_repository import BaseRepository


class VisualStyleRepository(BaseRepository[VisualStyleEntity, VisualStyle]):

    def __init__(self, session: Session):
        super().__init__(session, VisualStyleEntity)

    def _to_dto(self, entity: VisualStyleEntity) -> VisualStyle:
        return VisualStyle(
            id=entity.id,
            name=entity.name,
            is_default=entity.is_default,
            sample_image_path=entity.sample_image_path,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def _to_entity(self, dto: VisualStyle) -> VisualStyleEntity:
        entity = VisualStyleEntity(
            name=dto.name,
            is_default=dto.is_default,
            sample_image_path=dto.sample_image_path,
            created_at=dto.created_at,
            updated_at=dto.updated_at,
        )
        if dto.id > 0:
            entity.id = dto.id
        return entity

    def list_all(self) -> List[VisualStyle]:
        stmt = select(VisualStyleEntity).order_by(VisualStyleEntity.created_at.desc())
        entities = self.session.execute(stmt).scalars().all()
        return [self._to_dto(e) for e in entities]

    def exists_by_name(self, name: str, exclude_id: int | None = None) -> bool:
        stmt = select(VisualStyleEntity).where(VisualStyleEntity.name == name)
        if exclude_id is not None:
            stmt = stmt.where(VisualStyleEntity.id != exclude_id)
        entity = self.session.execute(stmt).scalars().first()
        return entity is not None

    def get_default_style(self) -> Optional[VisualStyle]:
        stmt = select(VisualStyleEntity).where(VisualStyleEntity.is_default == True)
        entity = self.session.execute(stmt).scalars().first()
        return self._to_dto(entity) if entity else None

    def clear_all_defaults(self) -> None:
        stmt = update(VisualStyleEntity).values(is_default=False)
        self.session.execute(stmt)

    def update_style(
        self,
        style_id: int,
        name: str,
        is_default: bool,
        sample_image_path: str,
    ) -> None:
        entity = self.session.get(VisualStyleEntity, style_id)
        if not entity:
            return

        entity.name = name
        entity.is_default = is_default
        entity.sample_image_path = sample_image_path
        entity.updated_at = int(datetime.now().timestamp() * 1000)
        self.session.commit()
