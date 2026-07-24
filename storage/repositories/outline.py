"""大纲 Repository。"""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.data_models import Outline, OutlineHistory
from storage.orm.models import OutlineEntity, OutlineHistoryEntity
from storage.repositories.base import BaseRepository


class OutlineRepository(BaseRepository[OutlineEntity, Outline]):
    """大纲 Repository。"""

    def __init__(self, session: Session):
        super().__init__(session, OutlineEntity)

    def _to_dto(self, entity: OutlineEntity) -> Outline:
        """Entity → DTO 转换。"""
        return Outline(
            id=entity.id if entity.id is not None else 0,
            project_id=entity.project_id,
            content=entity.content,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def _to_entity(self, dto: Outline) -> OutlineEntity:
        """DTO → Entity 转换。"""
        # 创建时不设置 id，让数据库自动生成；更新时从数据库加载现有 Entity
        entity = OutlineEntity(
            project_id=dto.project_id,
            content=dto.content,
            created_at=dto.created_at,
            updated_at=dto.updated_at,
        )
        return entity

    def get_by_project(self, project_id: int) -> Optional[Outline]:
        """
        查询项目的大纲。

        Args:
            project_id: 项目 ID

        Returns:
            大纲对象，如果不存在则返回 None
        """
        stmt = select(OutlineEntity).where(OutlineEntity.project_id == project_id)
        entity = self.session.execute(stmt).scalars().first()
        return self._to_dto(entity) if entity else None

    def update_content(self, outline_id: int, content: str, updated_at: int) -> None:
        """
        更新大纲内容。

        Args:
            outline_id: 大纲 ID
            content: 新内容
            updated_at: 更新时间（13位时间戳毫秒）
        """
        entity = self.session.get(OutlineEntity, outline_id)
        if not entity:
            return

        entity.content = content
        entity.updated_at = updated_at
        self.session.commit()


class OutlineHistoryRepository(BaseRepository[OutlineHistoryEntity, OutlineHistory]):
    """大纲历史 Repository。"""

    def __init__(self, session: Session):
        super().__init__(session, OutlineHistoryEntity)

    def _to_dto(self, entity: OutlineHistoryEntity) -> OutlineHistory:
        """Entity → DTO 转换。"""
        return OutlineHistory(
            id=entity.id if entity.id is not None else 0,
            outline_id=entity.outline_id,
            project_id=entity.project_id,
            content=entity.content,
            created_at=entity.created_at,
        )

    def _to_entity(self, dto: OutlineHistory) -> OutlineHistoryEntity:
        """DTO → Entity 转换。"""
        return OutlineHistoryEntity(
            id=dto.id,
            outline_id=dto.outline_id,
            project_id=dto.project_id,
            content=dto.content,
            created_at=dto.created_at,
        )

    def list_by_outline(self, outline_id: int) -> List[OutlineHistory]:
        """
        查询大纲的所有历史版本（按时间倒序）。

        Args:
            outline_id: 大纲 ID

        Returns:
            历史版本列表
        """
        stmt = (
            select(OutlineHistoryEntity)
            .where(OutlineHistoryEntity.outline_id == outline_id)
            .order_by(OutlineHistoryEntity.created_at.desc())
        )
        entities = self.session.execute(stmt).scalars().all()
        return [self._to_dto(e) for e in entities]
