"""剧本 Repository。"""

from typing import List, Optional

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from models.data_models import Script, ScriptHistory, Scene
from storage.orm.models import ScriptEntity, ScriptHistoryEntity, SceneEntity
from storage.repositories.base import BaseRepository


class ScriptRepository(BaseRepository[ScriptEntity, Script]):
    """剧本 Repository。"""

    def __init__(self, session: Session):
        super().__init__(session, ScriptEntity)

    def _to_dto(self, entity: ScriptEntity) -> Script:
        """Entity → DTO 转换。"""
        return Script(
            id=entity.id,
            project_id=entity.project_id,
            title=entity.title,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def _to_entity(self, dto: Script) -> ScriptEntity:
        """DTO → Entity 转换。"""
        return ScriptEntity(
            id=dto.id,
            project_id=dto.project_id,
            title=dto.title,
            created_at=dto.created_at,
            updated_at=dto.updated_at,
        )

    def get_by_project(self, project_id: str) -> Optional[Script]:
        """
        查询项目的剧本。

        Args:
            project_id: 项目 ID

        Returns:
            剧本对象，如果不存在则返回 None
        """
        stmt = select(ScriptEntity).where(ScriptEntity.project_id == project_id)
        entity = self.session.execute(stmt).scalars().first()
        return self._to_dto(entity) if entity else None

    def update_script(self, script_id: str, title: str, updated_at) -> None:
        """
        更新剧本。

        Args:
            script_id: 剧本 ID
            title: 标题
            updated_at: 更新时间
        """
        entity = self.session.get(ScriptEntity, script_id)
        if not entity:
            return

        entity.title = title
        entity.updated_at = updated_at
        self.session.commit()


class ScriptHistoryRepository(BaseRepository[ScriptHistoryEntity, ScriptHistory]):
    """剧本历史 Repository。"""

    def __init__(self, session: Session):
        super().__init__(session, ScriptHistoryEntity)

    def _to_dto(self, entity: ScriptHistoryEntity) -> ScriptHistory:
        """Entity → DTO 转换。"""
        return ScriptHistory(
            id=entity.id,
            script_id=entity.script_id,
            title=entity.title,
            scenes_snapshot=entity.scenes_snapshot,
            created_at=entity.created_at,
        )

    def _to_entity(self, dto: ScriptHistory) -> ScriptHistoryEntity:
        """DTO → Entity 转换。"""
        return ScriptHistoryEntity(
            id=dto.id,
            script_id=dto.script_id,
            title=dto.title,
            scenes_snapshot=dto.scenes_snapshot,
            created_at=dto.created_at,
        )

    def list_by_script(self, script_id: str) -> List[ScriptHistory]:
        """
        查询剧本的所有历史版本（按时间倒序）。

        Args:
            script_id: 剧本 ID

        Returns:
            历史版本列表
        """
        stmt = (
            select(ScriptHistoryEntity)
            .where(ScriptHistoryEntity.script_id == script_id)
            .order_by(ScriptHistoryEntity.created_at.desc())
        )
        entities = self.session.execute(stmt).scalars().all()
        return [self._to_dto(e) for e in entities]


class SceneRepository(BaseRepository[SceneEntity, Scene]):
    """场次 Repository。"""

    def __init__(self, session: Session):
        super().__init__(session, SceneEntity)

    def _to_dto(self, entity: SceneEntity) -> Scene:
        """Entity → DTO 转换。"""
        return Scene(
            id=entity.id,
            script_id=entity.script_id,
            scene_number=entity.scene_number,
            location_type=entity.location_type,
            location=entity.location,
            time_type=entity.time_type,
            time_detail=entity.time_detail,
            content=entity.content,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def _to_entity(self, dto: Scene) -> SceneEntity:
        """DTO → Entity 转换。"""
        return SceneEntity(
            id=dto.id,
            script_id=dto.script_id,
            scene_number=dto.scene_number,
            location_type=dto.location_type,
            location=dto.location,
            time_type=dto.time_type,
            time_detail=dto.time_detail,
            content=dto.content,
            created_at=dto.created_at,
            updated_at=dto.updated_at,
        )

    def list_by_script(self, script_id: str) -> List[Scene]:
        """
        查询剧本的所有场次（按场次号升序）。

        Args:
            script_id: 剧本 ID

        Returns:
            场次列表
        """
        stmt = (
            select(SceneEntity)
            .where(SceneEntity.script_id == script_id)
            .order_by(SceneEntity.scene_number.asc())
        )
        entities = self.session.execute(stmt).scalars().all()
        return [self._to_dto(e) for e in entities]

    def delete_by_script(self, script_id: str) -> None:
        """
        删除剧本的所有场次。

        Args:
            script_id: 剧本 ID
        """
        stmt = delete(SceneEntity).where(SceneEntity.script_id == script_id)
        self.session.execute(stmt)
        self.session.commit()
