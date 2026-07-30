"""活跃任务 Repository。"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.active_task import ActiveTask
from models.enums import TaskStatus
from storage.orm.project_entity import ActiveTaskEntity
from storage.repositories.base_repository import BaseRepository


class ActiveTaskRepository(BaseRepository[ActiveTaskEntity, ActiveTask]):
    """活跃任务 Repository。"""

    def __init__(self, session: Session):
        super().__init__(session, ActiveTaskEntity)

    def _to_dto(self, entity: ActiveTaskEntity) -> ActiveTask:
        """Entity → ActiveTask 转换。"""
        return ActiveTask(
            id=entity.id,
            provider_task_id=entity.provider_task_id,
            message_id=entity.message_id,
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

    def _to_entity(self, dto: ActiveTask) -> ActiveTaskEntity:
        """ActiveTask → Entity 转换。"""
        return ActiveTaskEntity(
            id=dto.id,
            provider_task_id=dto.provider_task_id,
            message_id=dto.message_id,
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
        message_id: str,
        provider_name: str,
        model_name: str,
        save_path: str,
        request_params: str,
        storyboard_id: int = 0,
    ) -> int:
        """
        添加新任务。

        Args:
            provider_task_id: Provider 返回的任务 ID
            message_id: 关联的消息 ID
            provider_name: Provider 名称
            model_name: 模型名称
            save_path: 保存路径
            request_params: 完整的 API 请求参数（JSON 字符串）
            storyboard_id: 关联的分镜 ID（可选）

        Returns:
            新记录的自增 ID
        """
        entity = ActiveTaskEntity(
            provider_task_id=provider_task_id,
            message_id=message_id,
            provider_name=provider_name,
            model_name=model_name,
            status="pending",
            completed=False,
            request_params=request_params,
            video_url="",
            save_path=save_path,
            error_message="",
            storyboard_id=storyboard_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        self.session.add(entity)
        self.session.flush()  # 刷新以获得自增 ID，但不提交事务
        return entity.id

    def list_active_tasks(self) -> List[dict]:
        """
        查询所有活跃任务（未完成的任务，按创建时间升序）。

        Returns:
            任务字典列表（保持向后兼容，返回 dict 而非 ActiveTask）
        """
        stmt = (
            select(ActiveTaskEntity)
            .where(ActiveTaskEntity.completed == False)
            .order_by(ActiveTaskEntity.created_at.asc())
        )
        entities = self.session.execute(stmt).scalars().all()
        return [
            {
                "id": e.id,
                "provider_task_id": e.provider_task_id,
                "message_id": e.message_id,
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
        """
        根据 ID 查询任务。

        Args:
            task_id: 任务 ID（自增主键）

        Returns:
            任务字典，如果不存在则返回 None
        """
        entity = self.session.get(ActiveTaskEntity, task_id)
        if not entity:
            return None
        return {
            "id": entity.id,
            "provider_task_id": entity.provider_task_id,
            "message_id": entity.message_id,
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
        """
        根据 provider_task_id 查询任务。

        Args:
            provider_task_id: Provider 返回的任务 ID

        Returns:
            任务字典，如果不存在则返回 None
        """
        stmt = select(ActiveTaskEntity).where(
            ActiveTaskEntity.provider_task_id == provider_task_id
        )
        entity = self.session.execute(stmt).scalar_one_or_none()
        if not entity:
            return None
        return {
            "id": entity.id,
            "provider_task_id": entity.provider_task_id,
            "message_id": entity.message_id,
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
        """
        更新任务状态。

        Args:
            task_id: 任务 ID（自增主键）
            status: 任务状态
            video_url: 视频 URL（可选）
            error_message: 错误信息（可选）
        """
        entity = self.session.get(ActiveTaskEntity, task_id)
        if not entity:
            return

        entity.status = status
        if video_url:
            entity.video_url = video_url
        if error_message:
            entity.error_message = error_message
        entity.updated_at = datetime.now()
        self.session.commit()

    def mark_completed(self, task_id: int) -> None:
        """
        标记任务为已完成。

        Args:
            task_id: 任务 ID（自增主键）
        """
        entity = self.session.get(ActiveTaskEntity, task_id)
        if not entity:
            return

        entity.completed = True
        entity.updated_at = datetime.now()
        self.session.commit()

    def list_completed_tasks(self, limit: int = 50, offset: int = 0) -> List[dict]:
        """
        查询已完成任务（分页，按更新时间降序）。

        Args:
            limit: 每页数量
            offset: 偏移量

        Returns:
            任务字典列表
        """
        stmt = (
            select(ActiveTaskEntity)
            .where(ActiveTaskEntity.completed == True)
            .order_by(ActiveTaskEntity.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        entities = self.session.execute(stmt).scalars().all()
        return [
            {
                "id": e.id,
                "provider_task_id": e.provider_task_id,
                "message_id": e.message_id,
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
