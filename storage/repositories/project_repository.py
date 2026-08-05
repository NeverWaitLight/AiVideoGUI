from datetime import datetime
from typing import List

from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from models.project import Project
from storage.orm.project_entity import ProjectEntity
from storage.repositories.base_repository import BaseRepository


class ProjectRepository(BaseRepository[ProjectEntity, Project]):

    def __init__(self, session: Session):
        super().__init__(session, ProjectEntity)

    def _to_dto(self, entity: ProjectEntity) -> Project:
        return Project(
            id=entity.id,
            name=entity.name,
            resolution=entity.resolution,
            aspect_ratio=entity.aspect_ratio,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            cover_image=entity.cover_image,
            visual_style_id=entity.visual_style_id,
        )

    def _to_entity(self, dto: Project) -> ProjectEntity:
        entity = ProjectEntity(
            name=dto.name,
            resolution=dto.resolution,
            aspect_ratio=dto.aspect_ratio,
            created_at=dto.created_at,
            updated_at=dto.updated_at,
            cover_image=dto.cover_image,
            visual_style_id=dto.visual_style_id,
        )
        if dto.id > 0:
            entity.id = dto.id
        return entity

    def list_all(self) -> List[Project]:
        stmt = select(ProjectEntity).order_by(ProjectEntity.created_at.desc())
        entities = self.session.execute(stmt).scalars().all()
        return [self._to_dto(e) for e in entities]

    def exists_by_name(self, name: str, exclude_id: int | None = None) -> bool:
        stmt = select(ProjectEntity).where(ProjectEntity.name == name)
        if exclude_id is not None:
            stmt = stmt.where(ProjectEntity.id != exclude_id)
        entity = self.session.execute(stmt).scalars().first()
        return entity is not None

    def update_project(
        self,
        project_id: int,
        name: str,
        resolution: str,
        aspect_ratio: str,
        cover_image: str = "",
        visual_style_id: int | None = None,
    ) -> None:
        entity = self.session.get(ProjectEntity, project_id)
        if not entity:
            return

        entity.name = name
        entity.resolution = resolution
        entity.aspect_ratio = aspect_ratio
        entity.cover_image = cover_image
        entity.visual_style_id = visual_style_id
        entity.updated_at = int(datetime.now().timestamp() * 1000)
        self.session.commit()

    def update_cover_image(self, project_id: int, cover_image: str) -> None:
        entity = self.session.get(ProjectEntity, project_id)
        if not entity:
            return

        entity.cover_image = cover_image
        entity.updated_at = int(datetime.now().timestamp() * 1000)
        self.session.commit()
