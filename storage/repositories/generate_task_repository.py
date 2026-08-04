import time
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.generate_task import GenerateTask
from models.enums import TaskStatus
from storage.orm.project_entity import GenerateTaskEntity
from storage.repositories.base_repository import BaseRepository


class GenerateTaskRepository(BaseRepository[GenerateTaskEntity, GenerateTask]):

    def __init__(self, session: Session):
        super().__init__(session, GenerateTaskEntity)

    def _to_dto(self, entity: GenerateTaskEntity) -> GenerateTask:
        return GenerateTask(
            id=entity.id,
            provider_task_id=entity.provider_task_id,
            provider_name=entity.provider_name,
            model_name=entity.model_name,
            status=entity.status,
            completed=entity.completed,
            request_params=entity.request_params,
            video_url=entity.video_url,
            save_path=entity.save_path,
            error_message=entity.error_message,
            storyboard_id=entity.storyboard_id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def _to_entity(self, dto: GenerateTask) -> GenerateTaskEntity:
        return GenerateTaskEntity(
            id=dto.id,
            provider_task_id=dto.provider_task_id,
            provider_name=dto.provider_name,
            model_name=dto.model_name,
            status=dto.status,
            completed=dto.completed,
            request_params=dto.request_params,
            video_url=dto.video_url,
            save_path=dto.save_path,
            error_message=dto.error_message,
            storyboard_id=dto.storyboard_id,
            created_at=dto.created_at,
            updated_at=dto.updated_at,
        )

    def add(
        self,
        provider_task_id: str,
        provider_name: str,
        model_name: str,
        save_path: str,
        request_params: str,
        storyboard_id: int = 0,
    ) -> int:
        entity = GenerateTaskEntity(
            provider_task_id=provider_task_id,
            provider_name=provider_name,
            model_name=model_name,
            status="pending",
            completed=False,
            request_params=request_params,
            video_url="",
            save_path=save_path,
            error_message="",
            storyboard_id=storyboard_id,
            created_at=int(time.time() * 1000),
            updated_at=int(time.time() * 1000),
        )
        self.session.add(entity)
        self.session.flush()
        return entity.id

    def list_active_tasks(self) -> List[dict]:
        stmt = (
            select(GenerateTaskEntity)
            .where(GenerateTaskEntity.completed == False)
            .order_by(GenerateTaskEntity.created_at.asc())
        )
        entities = self.session.execute(stmt).scalars().all()
        return [
            {
                "id": e.id,
                "provider_task_id": e.provider_task_id,
                "provider_name": e.provider_name,
                "model_name": e.model_name,
                "status": e.status,
                "completed": e.completed,
                "request_params": e.request_params,
                "video_url": e.video_url,
                "save_path": e.save_path,
                "error_message": e.error_message,
                "storyboard_id": e.storyboard_id,
                "created_at": e.created_at,
                "updated_at": e.updated_at,
            }
            for e in entities
        ]

    def get_by_id(self, task_id: int) -> Optional[dict]:
        entity = self.session.get(GenerateTaskEntity, task_id)
        if not entity:
            return None
        return {
            "id": entity.id,
            "provider_task_id": entity.provider_task_id,
            "provider_name": entity.provider_name,
            "model_name": entity.model_name,
            "status": entity.status,
            "completed": entity.completed,
            "request_params": entity.request_params,
            "video_url": entity.video_url,
            "save_path": entity.save_path,
            "error_message": entity.error_message,
            "storyboard_id": entity.storyboard_id,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
        }

    def get_by_provider_task_id(self, provider_task_id: str) -> Optional[dict]:
        stmt = select(GenerateTaskEntity).where(
            GenerateTaskEntity.provider_task_id == provider_task_id
        )
        entity = self.session.execute(stmt).scalar_one_or_none()
        if not entity:
            return None
        return {
            "id": entity.id,
            "provider_task_id": entity.provider_task_id,
            "provider_name": entity.provider_name,
            "model_name": entity.model_name,
            "status": entity.status,
            "completed": entity.completed,
            "request_params": entity.request_params,
            "video_url": entity.video_url,
            "save_path": entity.save_path,
            "error_message": entity.error_message,
            "storyboard_id": entity.storyboard_id,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
        }

    def update_status(
        self,
        task_id: int,
        status: str,
        video_url: str = "",
        error_message: str = "",
    ) -> None:
        entity = self.session.get(GenerateTaskEntity, task_id)
        if not entity:
            return

        entity.status = status
        if video_url:
            entity.video_url = video_url
        if error_message:
            entity.error_message = error_message
        entity.updated_at = int(time.time() * 1000)

    def mark_completed(self, task_id: int) -> None:
        entity = self.session.get(GenerateTaskEntity, task_id)
        if not entity:
            return

        entity.completed = True
        entity.updated_at = int(time.time() * 1000)

    def list_completed_tasks(self, limit: int = 50, offset: int = 0) -> List[dict]:
        stmt = (
            select(GenerateTaskEntity)
            .where(GenerateTaskEntity.completed == True)
            .order_by(GenerateTaskEntity.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        entities = self.session.execute(stmt).scalars().all()
        return [
            {
                "id": e.id,
                "provider_task_id": e.provider_task_id,
                "provider_name": e.provider_name,
                "model_name": e.model_name,
                "status": e.status,
                "completed": e.completed,
                "request_params": e.request_params,
                "video_url": e.video_url,
                "save_path": e.save_path,
                "error_message": e.error_message,
                "storyboard_id": e.storyboard_id,
                "created_at": e.created_at,
                "updated_at": e.updated_at,
            }
            for e in entities
        ]
