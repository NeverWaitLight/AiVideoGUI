"""角色 Repository。"""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.data_models import Character, CharacterHistory
from storage.orm.models import CharacterEntity, CharacterHistoryEntity
from storage.repositories.base import BaseRepository


class CharacterRepository(BaseRepository[CharacterEntity, Character]):
    """角色 Repository。"""

    def __init__(self, session: Session):
        super().__init__(session, CharacterEntity)

    def _to_dto(self, entity: CharacterEntity) -> Character:
        """Entity → DTO 转换。"""
        return Character(
            id=entity.id,
            project_id=entity.project_id,
            name=entity.name,
            ref_code=entity.ref_code,
            design_image=entity.design_image,
            description=entity.description,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def _to_entity(self, dto: Character) -> CharacterEntity:
        """DTO → Entity 转换。"""
        if dto.id == 0:
            return CharacterEntity(
                project_id=dto.project_id,
                name=dto.name,
                ref_code=dto.ref_code,
                design_image=dto.design_image,
                description=dto.description,
                created_at=dto.created_at if dto.created_at > 0 else None,
                updated_at=dto.updated_at if dto.updated_at > 0 else None,
            )
        else:
            return CharacterEntity(
                id=dto.id,
                project_id=dto.project_id,
                name=dto.name,
                ref_code=dto.ref_code,
                design_image=dto.design_image,
                description=dto.description,
                created_at=dto.created_at,
                updated_at=dto.updated_at,
            )

    def list_by_project(self, project_id: int) -> List[Character]:
        """查询项目的所有角色（按自增ID升序）。"""
        stmt = (
            select(CharacterEntity)
            .where(CharacterEntity.project_id == project_id)
            .order_by(CharacterEntity.id.asc())
        )
        entities = self.session.execute(stmt).scalars().all()
        return [self._to_dto(e) for e in entities]

    def get_by_ref_code(self, project_id: int, ref_code: str) -> Optional[Character]:
        """根据引用代号查询角色。"""
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
        """更新角色信息。"""
        entity = self.session.get(CharacterEntity, dto.id)
        if entity:
            entity.name = dto.name
            entity.ref_code = dto.ref_code
            entity.design_image = dto.design_image
            entity.description = dto.description
            self.session.commit()

    def batch_create(self, characters: List[Character]) -> None:
        """批量创建角色。"""
        for char in characters:
            entity = self._to_entity(char)
            self.session.add(entity)
        self.session.commit()


class CharacterHistoryRepository(BaseRepository[CharacterHistoryEntity, CharacterHistory]):
    """角色编辑历史 Repository。"""

    def __init__(self, session: Session):
        super().__init__(session, CharacterHistoryEntity)

    def _to_dto(self, entity: CharacterHistoryEntity) -> CharacterHistory:
        """Entity → DTO 转换。"""
        return CharacterHistory(
            id=entity.id,
            character_id=entity.character_id,
            snapshot=entity.snapshot,
            created_at=entity.created_at,
        )

    def _to_entity(self, dto: CharacterHistory) -> CharacterHistoryEntity:
        """DTO → Entity 转换。"""
        if dto.id == 0:
            return CharacterHistoryEntity(
                # 不设置 id，让数据库自动生成
                character_id=dto.character_id,
                snapshot=dto.snapshot,
                created_at=dto.created_at if dto.created_at > 0 else None,
            )
        else:
            return CharacterHistoryEntity(
                id=dto.id,
                character_id=dto.character_id,
                snapshot=dto.snapshot,
                created_at=dto.created_at,
            )

    def list_by_character(self, character_id: int) -> List[CharacterHistory]:
        """查询角色的所有编辑历史（按时间倒序）。"""
        stmt = (
            select(CharacterHistoryEntity)
            .where(CharacterHistoryEntity.character_id == character_id)
            .order_by(CharacterHistoryEntity.created_at.desc())
        )
        entities = self.session.execute(stmt).scalars().all()
        return [self._to_dto(e) for e in entities]
