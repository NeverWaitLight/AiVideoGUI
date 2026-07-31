from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.character import Character, CharacterHistory
from storage.orm.character_entity import CharacterEntity, CharacterHistoryEntity
from storage.repositories.base_repository import BaseRepository
from utils.path_converter import to_absolute_path


class CharacterRepository(BaseRepository[CharacterEntity, Character]):

    def __init__(self, session: Session, workspace_root: str = ""):
        super().__init__(session, CharacterEntity)
        self._workspace_root = workspace_root

    def get_by_id(self, id: str) -> Optional[Character]:
        stmt = select(CharacterEntity).where(CharacterEntity.uuid == id)
        entity = self.session.execute(stmt).scalar_one_or_none()
        return self._to_dto(entity) if entity else None

    def _to_dto(self, entity: CharacterEntity) -> Character:
        return Character(
            id=entity.id,
            uuid=entity.uuid,
            project_id=entity.project_id,
            name=entity.name,
            ref_code=entity.ref_code,
            design_image=to_absolute_path(entity.design_image, self._workspace_root),
            description=entity.description,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def _to_entity(self, dto: Character) -> CharacterEntity:
        entity = CharacterEntity(
            uuid=dto.uuid,
            project_id=dto.project_id,
            name=dto.name,
            ref_code=dto.ref_code,
            design_image=dto.design_image,
            description=dto.description,
            created_at=dto.created_at,
            updated_at=dto.updated_at,
        )
        if dto.id:
            entity.id = dto.id
        return entity

    def list_by_project(self, project_id: int) -> List[Character]:
        stmt = (
            select(CharacterEntity)
            .where(CharacterEntity.project_id == project_id)
            .order_by(CharacterEntity.id.asc())
        )
        entities = self.session.execute(stmt).scalars().all()
        return [self._to_dto(e) for e in entities]

    def get_by_ref_code(self, project_id: int, ref_code: str) -> Optional[Character]:
        stmt = (
            select(CharacterEntity)
            .where(
                CharacterEntity.project_id == project_id,
                CharacterEntity.ref_code == ref_code,
            )
        )
        entity = self.session.execute(stmt).scalar_one_or_none()
        return self._to_dto(entity) if entity else None

    def update(self, dto: Character) -> None:
        stmt = select(CharacterEntity).where(CharacterEntity.uuid == dto.uuid)
        entity = self.session.execute(stmt).scalar_one_or_none()
        if entity:
            entity.name = dto.name
            entity.ref_code = dto.ref_code
            entity.design_image = dto.design_image
            entity.description = dto.description
            entity.updated_at = datetime.now()

    def delete(self, id: str) -> bool:
        stmt = select(CharacterEntity).where(CharacterEntity.uuid == id)
        entity = self.session.execute(stmt).scalar_one_or_none()
        if entity:
            self.session.delete(entity)
            return True
        return False

    def batch_create(self, characters: List[Character]) -> None:
        for char in characters:
            entity = self._to_entity(char)
            self.session.add(entity)


class CharacterHistoryRepository(BaseRepository[CharacterHistoryEntity, CharacterHistory]):

    def __init__(self, session: Session):
        super().__init__(session, CharacterHistoryEntity)

    def _to_dto(self, entity: CharacterHistoryEntity) -> CharacterHistory:
        return CharacterHistory(
            id=entity.id,
            character_id=entity.character_id,
            project_id=entity.project_id,
            name=entity.name,
            ref_code=entity.ref_code,
            design_image=entity.design_image,
            description=entity.description,
            created_at=entity.created_at,
        )

    def _to_entity(self, dto: CharacterHistory) -> CharacterHistoryEntity:
        return CharacterHistoryEntity(
            character_id=dto.character_id,
            project_id=dto.project_id,
            name=dto.name,
            ref_code=dto.ref_code,
            design_image=dto.design_image,
            description=dto.description,
            created_at=dto.created_at,
        )

    def list_by_character(self, character_id: str) -> List[CharacterHistory]:
        stmt = (
            select(CharacterHistoryEntity)
            .where(CharacterHistoryEntity.character_id == character_id)
            .order_by(CharacterHistoryEntity.created_at.desc())
        )
        entities = self.session.execute(stmt).scalars().all()
        return [self._to_dto(e) for e in entities]
