"""分镜 Repository。"""

from typing import List

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from models.data_models import Shot, ShotHistory, ShotSize
from storage.orm.models import ShotEntity, ShotHistoryEntity, SceneEntity, ScriptEntity
from storage.repositories.base import BaseRepository


class ShotRepository(BaseRepository[ShotEntity, Shot]):
    """分镜 Repository。"""

    def __init__(self, session: Session):
        super().__init__(session, ShotEntity)

    def _to_dto(self, entity: ShotEntity) -> Shot:
        """Entity → DTO 转换。"""
        return Shot(
            id=entity.id,
            scene_id=entity.scene_id,
            scene_number=entity.scene_number,
            shot_number=entity.shot_number,
            design_image=entity.design_image,
            shot_size=ShotSize(entity.shot_size) if isinstance(entity.shot_size, str) else entity.shot_size,
            camera_movement=entity.camera_movement,
            visual_content=entity.visual_content,
            dialogue=entity.dialogue,
            sound_effect=entity.sound_effect,
            duration=entity.duration,
            notes=entity.notes,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def _to_entity(self, dto: Shot) -> ShotEntity:
        """DTO → Entity 转换。"""
        return ShotEntity(
            id=dto.id,
            scene_id=dto.scene_id,
            scene_number=dto.scene_number,
            shot_number=dto.shot_number,
            design_image=dto.design_image,
            shot_size=dto.shot_size.value if isinstance(dto.shot_size, ShotSize) else dto.shot_size,
            camera_movement=dto.camera_movement,
            visual_content=dto.visual_content,
            dialogue=dto.dialogue,
            sound_effect=dto.sound_effect,
            duration=dto.duration,
            notes=dto.notes,
            created_at=dto.created_at,
            updated_at=dto.updated_at,
        )

    def list_by_scene(self, scene_id: str) -> List[Shot]:
        """
        查询场次的所有分镜（按镜头号升序）。

        Args:
            scene_id: 场次 ID

        Returns:
            分镜列表
        """
        stmt = (
            select(ShotEntity)
            .where(ShotEntity.scene_id == scene_id)
            .order_by(ShotEntity.shot_number.asc())
        )
        entities = self.session.execute(stmt).scalars().all()
        return [self._to_dto(e) for e in entities]

    def list_by_project(self, project_id: str) -> List[Shot]:
        """
        查询项目的所有分镜（通过 JOIN 跨 3 表查询）。

        Args:
            project_id: 项目 ID

        Returns:
            分镜列表
        """
        stmt = (
            select(ShotEntity)
            .join(SceneEntity, ShotEntity.scene_id == SceneEntity.id)
            .join(ScriptEntity, SceneEntity.script_id == ScriptEntity.id)
            .where(ScriptEntity.project_id == project_id)
            .order_by(ShotEntity.scene_number.asc(), ShotEntity.shot_number.asc())
        )
        entities = self.session.execute(stmt).scalars().all()
        return [self._to_dto(e) for e in entities]

    def delete_by_scene(self, scene_id: str) -> None:
        """
        删除场次的所有分镜。

        Args:
            scene_id: 场次 ID
        """
        stmt = delete(ShotEntity).where(ShotEntity.scene_id == scene_id)
        self.session.execute(stmt)
        self.session.commit()


class ShotHistoryRepository(BaseRepository[ShotHistoryEntity, ShotHistory]):
    """分镜历史 Repository。"""

    def __init__(self, session: Session):
        super().__init__(session, ShotHistoryEntity)

    def _to_dto(self, entity: ShotHistoryEntity) -> ShotHistory:
        """Entity → DTO 转换。"""
        return ShotHistory(
            id=entity.id,
            project_id=entity.project_id,
            shots_snapshot=entity.shots_snapshot,
            created_at=entity.created_at,
        )

    def _to_entity(self, dto: ShotHistory) -> ShotHistoryEntity:
        """DTO → Entity 转换。"""
        return ShotHistoryEntity(
            id=dto.id,
            project_id=dto.project_id,
            shots_snapshot=dto.shots_snapshot,
            created_at=dto.created_at,
        )

    def list_by_project(self, project_id: str) -> List[ShotHistory]:
        """
        查询项目的所有分镜历史（按时间倒序）。

        Args:
            project_id: 项目 ID

        Returns:
            历史版本列表
        """
        stmt = (
            select(ShotHistoryEntity)
            .where(ShotHistoryEntity.project_id == project_id)
            .order_by(ShotHistoryEntity.created_at.desc())
        )
        entities = self.session.execute(stmt).scalars().all()
        return [self._to_dto(e) for e in entities]
