from typing import List, Optional

from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session

from models.enums import MediaType
from models.media_file import MediaFile
from storage.orm.media_entity import MediaFileEntity
from storage.repositories.base_repository import BaseRepository
from utils.path_converter import to_absolute_path, to_qml_local_path


class MediaRepository(BaseRepository[MediaFileEntity, MediaFile]):

    def __init__(self, session: Session, workspace_root: str = ""):
        super().__init__(session, MediaFileEntity)
        self._workspace_root = workspace_root

    def _to_dto(self, entity: MediaFileEntity) -> MediaFile:
        return MediaFile(
            id=entity.id,
            filename=entity.filename,
            media_type=MediaType(entity.media_type),
            local_path=to_qml_local_path(to_absolute_path(entity.local_path, self._workspace_root)),
            file_size=entity.file_size,
            source=entity.source,
            conversation_id=entity.conversation_id,
            message_id=entity.message_id,
            created_at=entity.created_at,
            thumbnail_path=to_qml_local_path(to_absolute_path(entity.thumbnail_path, self._workspace_root)),
            first_frame_path=to_qml_local_path(to_absolute_path(entity.first_frame_path, self._workspace_root)),
            last_frame_path=to_qml_local_path(to_absolute_path(entity.last_frame_path, self._workspace_root)),
            duration=entity.duration,
            width=entity.width,
            height=entity.height,
            storyboard_id=entity.storyboard_id,
            featured=entity.featured,
            generate_task_id=entity.generate_task_id or 0,
        )

    def _to_entity(self, dto: MediaFile) -> MediaFileEntity:
        return MediaFileEntity(
            id=dto.id,
            filename=dto.filename,
            media_type=dto.media_type.value,
            local_path=dto.local_path,
            file_size=dto.file_size,
            source=dto.source,
            conversation_id=dto.conversation_id,
            message_id=dto.message_id,
            created_at=dto.created_at,
            thumbnail_path=dto.thumbnail_path,
            first_frame_path=dto.first_frame_path,
            last_frame_path=dto.last_frame_path,
            duration=dto.duration,
            width=dto.width,
            height=dto.height,
            storyboard_id=dto.storyboard_id,
            featured=dto.featured,
            generate_task_id=dto.generate_task_id or 0,
        )

    def list_all(self, media_type: Optional[MediaType] = None) -> List[MediaFile]:
        stmt = select(MediaFileEntity).order_by(MediaFileEntity.created_at.desc())
        if media_type:
            stmt = stmt.where(MediaFileEntity.media_type == media_type.value)
        entities = self.session.execute(stmt).scalars().all()
        return [self._to_dto(e) for e in entities]

    def list_by_storyboard(self, storyboard_id: int) -> List[MediaFile]:
        stmt = (
            select(MediaFileEntity)
            .where(MediaFileEntity.storyboard_id == storyboard_id)
            .order_by(MediaFileEntity.created_at.desc())
        )
        entities = self.session.execute(stmt).scalars().all()
        return [self._to_dto(e) for e in entities]

    def set_featured(self, file_id: str, storyboard_id: int) -> None:
        stmt = select(MediaFileEntity).where(
            MediaFileEntity.storyboard_id == storyboard_id,
            MediaFileEntity.featured == True,
        )
        for entity in self.session.execute(stmt).scalars().all():
            entity.featured = False

        target = self.session.get(MediaFileEntity, file_id)
        if target:
            target.featured = True

    def update_metadata(
        self,
        file_id: str,
        thumbnail_path: str = "",
        first_frame_path: str = "",
        last_frame_path: str = "",
        duration: float = 0.0,
        width: int = 0,
        height: int = 0,
    ) -> None:
        entity = self.session.get(MediaFileEntity, file_id)
        if not entity:
            return

        if thumbnail_path:
            entity.thumbnail_path = thumbnail_path
        if first_frame_path:
            entity.first_frame_path = first_frame_path
        if last_frame_path:
            entity.last_frame_path = last_frame_path
        if duration > 0:
            entity.duration = duration
        if width > 0:
            entity.width = width
        if height > 0:
            entity.height = height

    def get_by_message_id(self, message_id: str) -> Optional[MediaFile]:
        stmt = select(MediaFileEntity).where(MediaFileEntity.message_id == message_id)
        entity = self.session.execute(stmt).scalar_one_or_none()
        return self._to_dto(entity) if entity else None

    def get_by_generate_task_id(self, generate_task_id: int) -> Optional[MediaFile]:
        if not generate_task_id:
            return None
        stmt = (
            select(MediaFileEntity)
            .where(MediaFileEntity.generate_task_id == generate_task_id)
            .order_by(MediaFileEntity.created_at.desc())
        )
        entity = self.session.execute(stmt).scalars().first()
        return self._to_dto(entity) if entity else None

    def list_with_filters(
        self,
        media_type: Optional[MediaType] = None,
        keyword: Optional[str] = None,
        conversation_ids: Optional[set[str]] = None,
        project_id: Optional[int] = None,
    ) -> List[MediaFile]:
        stmt = select(MediaFileEntity).order_by(MediaFileEntity.created_at.desc())

        if media_type:
            stmt = stmt.where(MediaFileEntity.media_type == media_type.value)

        if keyword:
            stmt = stmt.where(MediaFileEntity.filename.ilike(f"%{keyword}%"))

        if conversation_ids is not None:
            stmt = stmt.where(MediaFileEntity.conversation_id.in_(conversation_ids))

        if project_id is not None:
            from storage.orm.storyboard_entity import StoryboardEntity
            from storage.orm.screenplay_entity import ScreenplayEntity

            stmt = (
                stmt.join(StoryboardEntity, MediaFileEntity.storyboard_id == StoryboardEntity.id)
                .join(ScreenplayEntity, StoryboardEntity.scene_id == ScreenplayEntity.id)
                .where(ScreenplayEntity.project_id == project_id)
            )

        entities = self.session.execute(stmt).scalars().all()
        return [self._to_dto(e) for e in entities]

    def delete_by_project(self, project_id: int) -> int:
        """删除项目关联素材：按分镜归属或 local_path 前缀 projects/{id}/。"""
        from storage.orm.storyboard_entity import StoryboardEntity
        from storage.orm.screenplay_entity import ScreenplayEntity

        path_prefix = f"projects/{project_id}/"
        storyboard_ids = (
            select(StoryboardEntity.id)
            .join(ScreenplayEntity, StoryboardEntity.scene_id == ScreenplayEntity.id)
            .where(ScreenplayEntity.project_id == project_id)
        )
        stmt = delete(MediaFileEntity).where(
            or_(
                MediaFileEntity.storyboard_id.in_(storyboard_ids),
                MediaFileEntity.local_path.like(f"{path_prefix}%"),
            )
        )
        result = self.session.execute(stmt)
        return result.rowcount or 0

    def delete_by_ids(self, file_ids: List[str]) -> int:
        if not file_ids:
            return 0
        stmt = delete(MediaFileEntity).where(MediaFileEntity.id.in_(file_ids))
        result = self.session.execute(stmt)
        return result.rowcount or 0

    def list_featured_by_project(self, project_id: int) -> List[MediaFile]:
        from storage.orm.storyboard_entity import StoryboardEntity
        from storage.orm.screenplay_entity import ScreenplayEntity
        from sqlalchemy import func, case

        stmt = (
            select(MediaFileEntity)
            .join(StoryboardEntity, MediaFileEntity.storyboard_id == StoryboardEntity.id)
            .join(ScreenplayEntity, StoryboardEntity.scene_id == ScreenplayEntity.id)
            .where(
                ScreenplayEntity.project_id == project_id,
                MediaFileEntity.featured == True,
                MediaFileEntity.media_type == MediaType.VIDEO.value,
            )
            .order_by(StoryboardEntity.scene_number, StoryboardEntity.shot_number)
        )
        entities = self.session.execute(stmt).scalars().all()

        if entities:
            return [self._to_dto(e) for e in entities]

        subquery = (
            select(
                MediaFileEntity.storyboard_id,
                func.max(MediaFileEntity.filename).label('max_filename')
            )
            .where(MediaFileEntity.media_type == MediaType.VIDEO.value)
            .group_by(MediaFileEntity.storyboard_id)
            .subquery()
        )

        stmt = (
            select(MediaFileEntity)
            .join(StoryboardEntity, MediaFileEntity.storyboard_id == StoryboardEntity.id)
            .join(ScreenplayEntity, StoryboardEntity.scene_id == ScreenplayEntity.id)
            .join(
                subquery,
                (MediaFileEntity.storyboard_id == subquery.c.storyboard_id) &
                (MediaFileEntity.filename == subquery.c.max_filename)
            )
            .where(
                ScreenplayEntity.project_id == project_id,
                MediaFileEntity.media_type == MediaType.VIDEO.value,
            )
            .order_by(StoryboardEntity.scene_number, StoryboardEntity.shot_number)
        )
        entities = self.session.execute(stmt).scalars().all()
        return [self._to_dto(e) for e in entities]
