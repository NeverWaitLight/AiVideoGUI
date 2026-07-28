"""素材库 Repository。"""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.enums import MediaType
from models.media_file import MediaFile
from storage.orm.media_entity import MediaFileEntity
from storage.repositories.base_repository import BaseRepository


class MediaRepository(BaseRepository[MediaFileEntity, MediaFile]):
    """素材库 Repository。"""

    def __init__(self, session: Session):
        super().__init__(session, MediaFileEntity)

    def _to_dto(self, entity: MediaFileEntity) -> MediaFile:
        """Entity → DTO 转换。"""
        return MediaFile(
            id=entity.id,
            filename=entity.filename,
            media_type=MediaType(entity.media_type),
            local_path=entity.local_path,
            file_size=entity.file_size,
            source=entity.source,
            conversation_id=entity.conversation_id,
            message_id=entity.message_id,
            created_at=entity.created_at,
            thumbnail_path=entity.thumbnail_path,
            duration=entity.duration,
            width=entity.width,
            height=entity.height,
            storyboard_id=entity.storyboard_id,
            featured=entity.featured,
        )

    def _to_entity(self, dto: MediaFile) -> MediaFileEntity:
        """DTO → Entity 转换。"""
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
            duration=dto.duration,
            width=dto.width,
            height=dto.height,
            storyboard_id=dto.storyboard_id,
            featured=dto.featured,
        )

    def list_all(self, media_type: Optional[MediaType] = None) -> List[MediaFile]:
        """
        查询所有素材文件（按创建时间倒序）。

        Args:
            media_type: 素材类型过滤（可选）

        Returns:
            素材文件列表
        """
        stmt = select(MediaFileEntity).order_by(MediaFileEntity.created_at.desc())
        if media_type:
            stmt = stmt.where(MediaFileEntity.media_type == media_type.value)
        entities = self.session.execute(stmt).scalars().all()
        return [self._to_dto(e) for e in entities]

    def list_by_storyboard(self, storyboard_id: int) -> List[MediaFile]:
        """
        查询指定分镜关联的所有素材文件（按创建时间倒序）。

        Args:
            storyboard_id: 分镜 ID

        Returns:
            素材文件列表
        """
        stmt = (
            select(MediaFileEntity)
            .where(MediaFileEntity.storyboard_id == storyboard_id)
            .order_by(MediaFileEntity.created_at.desc())
        )
        entities = self.session.execute(stmt).scalars().all()
        return [self._to_dto(e) for e in entities]

    def set_featured(self, file_id: str, storyboard_id: int) -> None:
        """
        将指定文件设为分镜封面（同分镜下其他文件取消封面标记）。

        Args:
            file_id: 文件 ID
            storyboard_id: 分镜 ID
        """
        stmt = select(MediaFileEntity).where(
            MediaFileEntity.storyboard_id == storyboard_id,
            MediaFileEntity.featured == True,
        )
        for entity in self.session.execute(stmt).scalars().all():
            entity.featured = False

        target = self.session.get(MediaFileEntity, file_id)
        if target:
            target.featured = True
        # 移除 commit()，由外层 SessionManager 控制事务

    def update_metadata(
        self,
        file_id: str,
        thumbnail_path: str = "",
        duration: float = 0.0,
        width: int = 0,
        height: int = 0,
    ) -> None:
        """
        更新视频元数据。

        Args:
            file_id: 文件 ID
            thumbnail_path: 缩略图路径
            duration: 时长（秒）
            width: 宽度
            height: 高度
        """
        entity = self.session.get(MediaFileEntity, file_id)
        if not entity:
            return

        if thumbnail_path:
            entity.thumbnail_path = thumbnail_path
        if duration > 0:
            entity.duration = duration
        if width > 0:
            entity.width = width
        if height > 0:
            entity.height = height
        # 移除 commit()，由外层 SessionManager 控制事务

    def get_by_message_id(self, message_id: str) -> Optional[MediaFile]:
        """
        根据消息 ID 查询素材文件。

        Args:
            message_id: 消息 ID

        Returns:
            素材文件，如果不存在则返回 None
        """
        stmt = select(MediaFileEntity).where(MediaFileEntity.message_id == message_id)
        entity = self.session.execute(stmt).scalar_one_or_none()
        return self._to_dto(entity) if entity else None

    def list_with_filters(
        self,
        media_type: Optional[MediaType] = None,
        keyword: Optional[str] = None,
        conversation_ids: Optional[set[str]] = None,
    ) -> List[MediaFile]:
        """
        查询素材文件（支持多种过滤条件）。

        Args:
            media_type: 素材类型过滤
            keyword: 关键词过滤（文件名）
            conversation_ids: 对话 ID 集合过滤

        Returns:
            素材文件列表
        """
        stmt = select(MediaFileEntity).order_by(MediaFileEntity.created_at.desc())

        if media_type:
            stmt = stmt.where(MediaFileEntity.media_type == media_type.value)

        if keyword:
            stmt = stmt.where(MediaFileEntity.filename.ilike(f"%{keyword}%"))

        if conversation_ids is not None:
            stmt = stmt.where(MediaFileEntity.conversation_id.in_(conversation_ids))

        entities = self.session.execute(stmt).scalars().all()
        return [self._to_dto(e) for e in entities]
