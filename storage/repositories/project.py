"""项目 Repository。"""

from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.data_models import Project
from storage.orm.models import ProjectEntity
from storage.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[ProjectEntity, Project]):
    """项目 Repository。"""

    def __init__(self, session: Session):
        super().__init__(session, ProjectEntity)

    def _to_dto(self, entity: ProjectEntity) -> Project:
        """Entity → DTO 转换。"""
        return Project(
            id=entity.id,
            name=entity.name,
            resolution=entity.resolution,
            aspect_ratio=entity.aspect_ratio,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            cover_image=entity.cover_image,
        )

    def _to_entity(self, dto: Project) -> ProjectEntity:
        """DTO → Entity 转换。"""
        # 如果 ID 为 0，则不设置 ID，让数据库自动分配
        if dto.id == 0:
            return ProjectEntity(
                name=dto.name,
                resolution=dto.resolution,
                aspect_ratio=dto.aspect_ratio,
                cover_image=dto.cover_image,
                created_at=dto.created_at if dto.created_at > 0 else None,
                updated_at=dto.updated_at if dto.updated_at > 0 else None,
            )
        else:
            return ProjectEntity(
                id=dto.id,
                name=dto.name,
                resolution=dto.resolution,
                aspect_ratio=dto.aspect_ratio,
                created_at=dto.created_at,
                updated_at=dto.updated_at,
                cover_image=dto.cover_image,
            )

    def list_all(self) -> List[Project]:
        """查询所有项目（按创建时间倒序）。"""
        stmt = select(ProjectEntity).order_by(ProjectEntity.created_at.desc())
        entities = self.session.execute(stmt).scalars().all()
        return [self._to_dto(e) for e in entities]

    def update_project(
        self,
        project_id: int,
        name: str,
        resolution: str,
        aspect_ratio: str,
        cover_image: str = "",
    ) -> None:
        """
        更新项目信息。

        Args:
            project_id: 项目 ID
            name: 项目名称
            resolution: 分辨率
            aspect_ratio: 宽高比
            cover_image: 封面图片路径
        """
        entity = self.session.get(ProjectEntity, project_id)
        if not entity:
            return

        entity.name = name
        entity.resolution = resolution
        entity.aspect_ratio = aspect_ratio
        entity.cover_image = cover_image
        self.session.commit()
