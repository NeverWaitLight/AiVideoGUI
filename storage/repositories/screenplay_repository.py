"""剧本 Repository（场次表）。"""

from typing import List, Optional

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from models.enums import SceneLocation, SceneTime
from models.scene import Scene, ScreenplayHistory
from storage.orm.screenplay_entity import ScreenplayEntity, ScreenplayHistoryEntity
from storage.repositories.base_repository import BaseRepository


class ScreenplayRepository(BaseRepository[ScreenplayEntity, Scene]):
    """场次 Repository（screenplay 表）。"""

    def __init__(self, session: Session):
        super().__init__(session, ScreenplayEntity)

    def _to_dto(self, entity: ScreenplayEntity) -> Scene:
        """Entity → DTO 转换。"""
        return Scene(
            id=entity.id,
            project_id=entity.project_id,
            scene_number=entity.scene_number,
            location_type=SceneLocation(entity.location_type) if isinstance(entity.location_type, str) else entity.location_type,
            location=entity.location,
            time_type=SceneTime(entity.time_type) if isinstance(entity.time_type, str) else entity.time_type,
            time_detail=entity.time_detail,
            content=entity.content,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def _to_entity(self, dto: Scene) -> ScreenplayEntity:
        """DTO → Entity 转换。"""
        return ScreenplayEntity(
            id=dto.id if dto.id else None,  # 0 转为 None 以触发自增
            project_id=dto.project_id,
            scene_number=dto.scene_number,
            location_type=dto.location_type.value if isinstance(dto.location_type, SceneLocation) else dto.location_type,
            location=dto.location,
            time_type=dto.time_type.value if isinstance(dto.time_type, SceneTime) else dto.time_type,
            time_detail=dto.time_detail,
            content=dto.content,
            created_at=dto.created_at,
            updated_at=dto.updated_at,
        )

    def list_by_project(self, project_id: int) -> List[Scene]:
        """
        查询项目的所有场次（按场次号升序）。

        Args:
            project_id: 项目 ID

        Returns:
            场次列表
        """
        stmt = (
            select(ScreenplayEntity)
            .where(ScreenplayEntity.project_id == project_id)
            .order_by(ScreenplayEntity.scene_number.asc())
        )
        entities = self.session.execute(stmt).scalars().all()
        return [self._to_dto(e) for e in entities]

    def get_by_scene_number(self, project_id: int, scene_number: int) -> Optional[Scene]:
        """
        查询项目中的指定场次。

        Args:
            project_id: 项目 ID
            scene_number: 场次号

        Returns:
            场次对象，如果不存在则返回 None
        """
        stmt = select(ScreenplayEntity).where(
            ScreenplayEntity.project_id == project_id,
            ScreenplayEntity.scene_number == scene_number
        )
        entity = self.session.execute(stmt).scalars().first()
        return self._to_dto(entity) if entity else None

    def delete_by_project(self, project_id: int) -> None:
        """
        删除项目的所有场次。

        Args:
            project_id: 项目 ID
        """
        stmt = delete(ScreenplayEntity).where(ScreenplayEntity.project_id == project_id)
        self.session.execute(stmt)
        # 不要在这里 commit，由 SessionManager 管理事务


class ScreenplayHistoryRepository(BaseRepository[ScreenplayHistoryEntity, ScreenplayHistory]):
    """剧本历史 Repository。"""

    def __init__(self, session: Session):
        super().__init__(session, ScreenplayHistoryEntity)

    def _to_dto(self, entity: ScreenplayHistoryEntity) -> ScreenplayHistory:
        """Entity → DTO 转换。"""
        return ScreenplayHistory(
            id=entity.id if entity.id is not None else 0,
            screenplay_id=entity.screenplay_id,
            project_id=entity.project_id,
            scene_number=entity.scene_number,
            location_type=SceneLocation(entity.location_type) if isinstance(entity.location_type, str) else entity.location_type,
            location=entity.location,
            time_type=SceneTime(entity.time_type) if isinstance(entity.time_type, str) else entity.time_type,
            time_detail=entity.time_detail,
            content=entity.content,
            created_at=entity.created_at,
        )

    def _to_entity(self, dto: ScreenplayHistory) -> ScreenplayHistoryEntity:
        """DTO → Entity 转换。"""
        return ScreenplayHistoryEntity(
            id=dto.id if dto.id else None,  # 0 转为 None 以触发自增
            screenplay_id=dto.screenplay_id,
            project_id=dto.project_id,
            scene_number=dto.scene_number,
            location_type=dto.location_type.value if isinstance(dto.location_type, SceneLocation) else dto.location_type,
            location=dto.location,
            time_type=dto.time_type.value if isinstance(dto.time_type, SceneTime) else dto.time_type,
            time_detail=dto.time_detail,
            content=dto.content,
            created_at=dto.created_at,
        )

    def list_by_screenplay(self, screenplay_id: int) -> List[ScreenplayHistory]:
        """
        查询单个场次的所有历史版本（按时间倒序）。

        Args:
            screenplay_id: 场次 ID

        Returns:
            历史版本列表
        """
        stmt = (
            select(ScreenplayHistoryEntity)
            .where(ScreenplayHistoryEntity.screenplay_id == screenplay_id)
            .order_by(ScreenplayHistoryEntity.created_at.desc())
        )
        entities = self.session.execute(stmt).scalars().all()
        return [self._to_dto(e) for e in entities]

    def list_by_project(self, project_id: int) -> List[ScreenplayHistory]:
        """
        查询项目的所有历史版本（按时间倒序）。

        Args:
            project_id: 项目 ID

        Returns:
            历史版本列表
        """
        stmt = (
            select(ScreenplayHistoryEntity)
            .where(ScreenplayHistoryEntity.project_id == project_id)
            .order_by(ScreenplayHistoryEntity.created_at.desc())
        )
        entities = self.session.execute(stmt).scalars().all()
        return [self._to_dto(e) for e in entities]

    def list_by_project_and_timestamp(self, project_id: int, created_at: int) -> List[ScreenplayHistory]:
        """
        查询项目在指定时间戳保存的所有场次历史（一次快照）。

        Args:
            project_id: 项目 ID
            created_at: 保存时间戳（毫秒）

        Returns:
            该次快照的所有场次历史
        """
        stmt = (
            select(ScreenplayHistoryEntity)
            .where(
                ScreenplayHistoryEntity.project_id == project_id,
                ScreenplayHistoryEntity.created_at == created_at,
            )
            .order_by(ScreenplayHistoryEntity.scene_number.asc())
        )
        entities = self.session.execute(stmt).scalars().all()
        return [self._to_dto(e) for e in entities]

    def distinct_timestamps_by_project(self, project_id: int) -> List[int]:
        """
        查询项目的所有不同保存时间戳（按时间倒序）。

        Args:
            project_id: 项目 ID

        Returns:
            去重的时间戳列表
        """
        from sqlalchemy import distinct

        stmt = (
            select(distinct(ScreenplayHistoryEntity.created_at))
            .where(ScreenplayHistoryEntity.project_id == project_id)
            .order_by(ScreenplayHistoryEntity.created_at.desc())
        )
        return list(self.session.execute(stmt).scalars().all())
