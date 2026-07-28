"""Repository 层基类。"""

from typing import Generic, List, Optional, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from storage.orm.base import Base

EntityType = TypeVar("EntityType", bound=Base)
DTOType = TypeVar("DTOType")


class BaseRepository(Generic[EntityType, DTOType]):
    """
    通用 Repository 基类。

    提供基础 CRUD 操作和 Entity ↔ DTO 转换接口。
    子类需实现 _to_dto() 和 _to_entity() 方法。
    """

    def __init__(self, session: Session, entity_class: Type[EntityType]):
        """
        初始化 Repository。

        Args:
            session: SQLAlchemy Session 实例
            entity_class: ORM 实体类
        """
        self.session = session
        self.entity_class = entity_class

    def _to_dto(self, entity: EntityType) -> DTOType:
        """
        Entity → DTO 转换（子类实现）。

        Args:
            entity: ORM 实体对象

        Returns:
            DTO 对象
        """
        raise NotImplementedError("子类必须实现 _to_dto() 方法")

    def _to_entity(self, dto: DTOType) -> EntityType:
        """
        DTO → Entity 转换（子类实现）。

        Args:
            dto: DTO 对象

        Returns:
            ORM 实体对象
        """
        raise NotImplementedError("子类必须实现 _to_entity() 方法")

    def get_by_id(self, id: str | int) -> Optional[DTOType]:
        """
        根据 ID 查询单个记录。

        Args:
            id: 记录 ID

        Returns:
            DTO 对象，如果不存在则返回 None
        """
        entity = self.session.get(self.entity_class, id)
        return self._to_dto(entity) if entity else None

    def save(self, dto: DTOType) -> DTOType:
        """
        保存记录（新增或更新）。

        如果 DTO 的 ID 为 0 或 None，则创建新记录；否则更新现有记录。

        Args:
            dto: DTO 对象

        Returns:
            保存后的 DTO 对象（包含数据库生成的字段）
        """
        entity = self._to_entity(dto)
        # 使用 merge() 处理新增和更新：
        # - 如果 entity.id 在 session 中不存在，执行 INSERT
        # - 如果 entity.id 已存在，执行 UPDATE
        merged_entity = self.session.merge(entity)
        self.session.flush()  # flush 后数据库生成的 ID 会自动填充到 entity
        return self._to_dto(merged_entity)

    def update(self, dto: DTOType) -> DTOType:
        """
        更新记录（save() 的别名）。

        Args:
            dto: DTO 对象

        Returns:
            更新后的 DTO 对象
        """
        return self.save(dto)

    def create(self, dto: DTOType) -> DTOType:
        """
        创建新记录。

        Args:
            dto: DTO 对象

        Returns:
            创建后的 DTO 对象（包含数据库生成的字段）
        """
        entity = self._to_entity(dto)
        self.session.add(entity)
        self.session.flush()  # flush 后数据库生成的 ID 会自动填充到 entity
        self.session.commit()
        return self._to_dto(entity)

    def delete(self, id: str | int) -> bool:
        """
        删除记录。

        Args:
            id: 记录 ID

        Returns:
            是否删除成功
        """
        entity = self.session.get(self.entity_class, id)
        if entity:
            self.session.delete(entity)
            self.session.commit()
            return True
        return False

    def list_all(self) -> List[DTOType]:
        """
        查询所有记录。

        Returns:
            DTO 对象列表
        """
        stmt = select(self.entity_class)
        entities = self.session.execute(stmt).scalars().all()
        return [self._to_dto(e) for e in entities]

    def commit(self) -> None:
        """提交当前事务。"""
        self.session.commit()

    def rollback(self) -> None:
        """回滚当前事务。"""
        self.session.rollback()
