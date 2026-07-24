"""剧本 Repository（场次表）。"""

from typing import List, Optional

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from models.data_models import SceneLocation, SceneTime, Scene, ScriptHistory
from storage.orm.models import ScriptEntity, ScriptHistoryEntity
from storage.repositories.base import BaseRepository


class ScriptRepository(BaseRepository[ScriptEntity, Scene]):
    """场次 Repository（scripts 表现在就是场次表）。"""

    def __init__(self, session: Session):
        super().__init__(session, ScriptEntity)

    def _to_dto(self, entity: ScriptEntity) -> Scene:
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

    def _to_entity(self, dto: Scene) -> ScriptEntity:
        """DTO → Entity 转换。"""
        return ScriptEntity(
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
            select(ScriptEntity)
            .where(ScriptEntity.project_id == project_id)
            .order_by(ScriptEntity.scene_number.asc())
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
        stmt = select(ScriptEntity).where(
            ScriptEntity.project_id == project_id,
            ScriptEntity.scene_number == scene_number
        )
        entity = self.session.execute(stmt).scalars().first()
        return self._to_dto(entity) if entity else None

    def delete_by_project(self, project_id: int) -> None:
        """
        删除项目的所有场次。

        Args:
            project_id: 项目 ID
        """
        stmt = delete(ScriptEntity).where(ScriptEntity.project_id == project_id)
        self.session.execute(stmt)
        self.session.commit()


class ScriptHistoryRepository(BaseRepository[ScriptHistoryEntity, ScriptHistory]):
    """剧本历史 Repository。"""

    def __init__(self, session: Session):
        super().__init__(session, ScriptHistoryEntity)

    def _to_dto(self, entity: ScriptHistoryEntity) -> ScriptHistory:
        """Entity → DTO 转换。"""
        return ScriptHistory(
            id=entity.id,
            project_id=entity.project_id,
            scenes_snapshot=entity.scenes_snapshot,
            created_at=entity.created_at,
        )

    def _to_entity(self, dto: ScriptHistory) -> ScriptHistoryEntity:
        """DTO → Entity 转换。"""
        return ScriptHistoryEntity(
            id=dto.id,
            project_id=dto.project_id,
            scenes_snapshot=dto.scenes_snapshot,
            created_at=dto.created_at,
        )

    def list_by_project(self, project_id: int) -> List[ScriptHistory]:
        """
        查询项目的所有历史版本（按时间倒序）。

        Args:
            project_id: 项目 ID

        Returns:
            历史版本列表
        """
        stmt = (
            select(ScriptHistoryEntity)
            .where(ScriptHistoryEntity.project_id == project_id)
            .order_by(ScriptHistoryEntity.created_at.desc())
        )
        entities = self.session.execute(stmt).scalars().all()
        return [self._to_dto(e) for e in entities]
