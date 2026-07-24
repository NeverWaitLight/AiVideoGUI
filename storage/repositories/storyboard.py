"""分镜 Repository。"""

from typing import List

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from models.data_models import Storyboard, StoryboardHistory, ShotSize
from storage.orm.models import StoryboardEntity, StoryboardHistoryEntity, ScreenplayEntity
from storage.repositories.base import BaseRepository


class StoryboardRepository(BaseRepository[StoryboardEntity, Storyboard]):
    """分镜 Repository。"""

    def __init__(self, session: Session):
        super().__init__(session, StoryboardEntity)

    def _to_dto(self, entity: StoryboardEntity) -> Storyboard:
        """Entity → DTO 转换。"""
        return Storyboard(
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

    def _to_entity(self, dto: Storyboard) -> StoryboardEntity:
        """DTO → Entity 转换。"""
        return StoryboardEntity(
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

    def list_by_scene(self, scene_id: int) -> List[Storyboard]:
        """查询场次的所有分镜（按镜头号升序）。"""
        stmt = (
            select(StoryboardEntity)
            .where(StoryboardEntity.scene_id == scene_id)
            .order_by(StoryboardEntity.shot_number.asc())
        )
        entities = self.session.execute(stmt).scalars().all()
        return [self._to_dto(e) for e in entities]

    def list_by_project(self, project_id: int) -> List[Storyboard]:
        """查询项目的所有分镜（通过 JOIN 查询）。"""
        stmt = (
            select(StoryboardEntity)
            .join(ScreenplayEntity, StoryboardEntity.scene_id == ScreenplayEntity.id)
            .where(ScreenplayEntity.project_id == project_id)
            .order_by(StoryboardEntity.scene_number.asc(), StoryboardEntity.shot_number.asc())
        )
        entities = self.session.execute(stmt).scalars().all()
        return [self._to_dto(e) for e in entities]

    def delete_by_scene(self, scene_id: int) -> None:
        """删除场次的所有分镜。"""
        stmt = delete(StoryboardEntity).where(StoryboardEntity.scene_id == scene_id)
        self.session.execute(stmt)
        self.session.commit()

    def delete_by_project(self, project_id: int) -> None:
        """删除项目的所有分镜（通过 JOIN 查询）。"""
        stmt = (
            delete(StoryboardEntity)
            .where(
                StoryboardEntity.scene_id.in_(
                    select(ScreenplayEntity.id).where(ScreenplayEntity.project_id == project_id)
                )
            )
        )
        self.session.execute(stmt)
        self.session.commit()


class StoryboardHistoryRepository(BaseRepository[StoryboardHistoryEntity, StoryboardHistory]):
    """分镜历史 Repository。"""

    def __init__(self, session: Session):
        super().__init__(session, StoryboardHistoryEntity)

    def _to_dto(self, entity: StoryboardHistoryEntity) -> StoryboardHistory:
        """Entity → DTO 转换。"""
        return StoryboardHistory(
            id=entity.id,
            storyboard_id=entity.storyboard_id,
            project_id=entity.project_id,
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
        )

    def _to_entity(self, dto: StoryboardHistory) -> StoryboardHistoryEntity:
        """DTO → Entity 转换。"""
        return StoryboardHistoryEntity(
            storyboard_id=dto.storyboard_id,
            project_id=dto.project_id,
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
        )

    def list_by_project(self, project_id: int) -> List[StoryboardHistory]:
        """查询项目的所有分镜历史（按时间倒序）。"""
        stmt = (
            select(StoryboardHistoryEntity)
            .where(StoryboardHistoryEntity.project_id == project_id)
            .order_by(StoryboardHistoryEntity.created_at.desc())
        )
        entities = self.session.execute(stmt).scalars().all()
        return [self._to_dto(e) for e in entities]

    def distinct_timestamps_by_project(self, project_id: int) -> List[int]:
        """查询项目的所有不同保存时间戳（按时间倒序）。"""
        stmt = (
            select(StoryboardHistoryEntity.created_at)
            .where(StoryboardHistoryEntity.project_id == project_id)
            .distinct()
            .order_by(StoryboardHistoryEntity.created_at.desc())
        )
        return list(self.session.execute(stmt).scalars().all())

    def list_by_project_and_timestamp(
        self, project_id: int, created_at: int
    ) -> List[StoryboardHistory]:
        """查询项目在指定时间戳保存的所有分镜历史。"""
        stmt = (
            select(StoryboardHistoryEntity)
            .where(
                StoryboardHistoryEntity.project_id == project_id,
                StoryboardHistoryEntity.created_at == created_at,
            )
            .order_by(StoryboardHistoryEntity.scene_number.asc(), StoryboardHistoryEntity.shot_number.asc())
        )
        entities = self.session.execute(stmt).scalars().all()
        return [self._to_dto(e) for e in entities]
