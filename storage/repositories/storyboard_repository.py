from typing import List

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from models.enums import ShotSize
from models.storyboard import Storyboard, StoryboardHistory
from storage.orm.storyboard_entity import StoryboardEntity, StoryboardHistoryEntity
from storage.orm.screenplay_entity import ScreenplayEntity
from storage.repositories.base_repository import BaseRepository
from utils.path_converter import to_absolute_path


class StoryboardRepository(BaseRepository[StoryboardEntity, Storyboard]):

    def __init__(self, session: Session, workspace_root: str = ""):
        super().__init__(session, StoryboardEntity)
        self._workspace_root = workspace_root

    def _to_dto(self, entity: StoryboardEntity) -> Storyboard:
        return Storyboard(
            id=entity.id,
            scene_id=entity.scene_id,
            scene_number=entity.scene_number,
            shot_number=entity.shot_number,
            design_image=to_absolute_path(entity.design_image, self._workspace_root),
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
        entity = StoryboardEntity(
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
        if dto.id > 0:
            entity.id = dto.id
        return entity

    def list_by_scene(self, scene_id: int) -> List[Storyboard]:
        stmt = (
            select(StoryboardEntity)
            .where(StoryboardEntity.scene_id == scene_id)
            .order_by(StoryboardEntity.shot_number.asc())
        )
        entities = self.session.execute(stmt).scalars().all()
        return [self._to_dto(e) for e in entities]

    def list_by_project(self, project_id: int) -> List[Storyboard]:
        # 清除 Session 缓存，确保获取最新数据
        self.session.expire_all()

        # 先获取该项目的所有有效场次 ID
        valid_scene_ids_stmt = select(ScreenplayEntity.id).where(ScreenplayEntity.project_id == project_id)
        valid_scene_ids = set(self.session.execute(valid_scene_ids_stmt).scalars().all())

        # 查询所有分镜（不使用 JOIN）
        all_storyboards_stmt = select(StoryboardEntity).order_by(
            StoryboardEntity.scene_number.asc(),
            StoryboardEntity.shot_number.asc()
        )
        all_entities = self.session.execute(all_storyboards_stmt).scalars().all()

        # 在 Python 层过滤：只保留 scene_id 在有效场次列表中的分镜
        entities = [e for e in all_entities if e.scene_id in valid_scene_ids]

        return [self._to_dto(e) for e in entities]

    def delete_by_scene(self, scene_id: int) -> None:
        stmt = delete(StoryboardEntity).where(StoryboardEntity.scene_id == scene_id)
        self.session.execute(stmt)
        self.session.commit()

    def delete_by_project(self, project_id: int) -> None:
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

    def __init__(self, session: Session):
        super().__init__(session, StoryboardHistoryEntity)

    def _to_dto(self, entity: StoryboardHistoryEntity) -> StoryboardHistory:
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
        stmt = (
            select(StoryboardHistoryEntity)
            .where(StoryboardHistoryEntity.project_id == project_id)
            .order_by(StoryboardHistoryEntity.created_at.desc())
        )
        entities = self.session.execute(stmt).scalars().all()
        return [self._to_dto(e) for e in entities]

    def distinct_timestamps_by_project(self, project_id: int) -> List[int]:
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
