from typing import Generic, List, Optional, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from storage.orm.base import Base

EntityType = TypeVar("EntityType", bound=Base)
DTOType = TypeVar("DTOType")


class BaseRepository(Generic[EntityType, DTOType]):

    def __init__(self, session: Session, entity_class: Type[EntityType]):
        self.session = session
        self.entity_class = entity_class

    def _to_dto(self, entity: EntityType) -> DTOType:
        raise NotImplementedError("子类必须实现 _to_dto() 方法")

    def _to_entity(self, dto: DTOType) -> EntityType:
        raise NotImplementedError("子类必须实现 _to_entity() 方法")

    def get_by_id(self, id: str | int) -> Optional[DTOType]:
        entity = self.session.get(self.entity_class, id)
        return self._to_dto(entity) if entity else None

    def save(self, dto: DTOType) -> DTOType:
        entity = self._to_entity(dto)
        merged_entity = self.session.merge(entity)
        self.session.flush()
        return self._to_dto(merged_entity)

    def update(self, dto: DTOType) -> DTOType:
        return self.save(dto)

    def create(self, dto: DTOType) -> DTOType:
        entity = self._to_entity(dto)
        self.session.add(entity)
        self.session.flush()
        self.session.commit()
        return self._to_dto(entity)

    def delete(self, id: str | int) -> bool:
        entity = self.session.get(self.entity_class, id)
        if entity:
            self.session.delete(entity)
            self.session.commit()
            return True
        return False

    def list_all(self) -> List[DTOType]:
        stmt = select(self.entity_class)
        entities = self.session.execute(stmt).scalars().all()
        return [self._to_dto(e) for e in entities]

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()
