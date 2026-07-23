"""活跃任务 Repository。"""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from storage.orm.models import ActiveTaskEntity
from storage.repositories.base import BaseRepository


class ActiveTaskRepository(BaseRepository[ActiveTaskEntity, dict]):
    """活跃任务 Repository。"""

    def __init__(self, session: Session):
        super().__init__(session, ActiveTaskEntity)

    def _to_dto(self, entity: ActiveTaskEntity) -> dict:
        """
        Entity → dict 转换。

        注意：active_tasks 表没有对应的 dataclass，直接返回字典。
        """
        return {
            "task_id": entity.task_id,
            "message_id": entity.message_id,
            "provider_name": entity.provider_name,
            "model_name": entity.model_name,
            "video_url": entity.video_url,
            "status": entity.status,
            "save_path": entity.save_path,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
        }

    def _to_entity(self, dto: dict) -> ActiveTaskEntity:
        """dict → Entity 转换。"""
        return ActiveTaskEntity(
            task_id=dto["task_id"],
            message_id=dto["message_id"],
            provider_name=dto["provider_name"],
            model_name=dto.get("model_name", ""),
            video_url=dto.get("video_url", ""),
            status=dto.get("status", "pending"),
            save_path=dto.get("save_path", ""),
            created_at=dto.get("created_at") if dto.get("created_at", 0) > 0 else None,
            updated_at=dto.get("updated_at") if dto.get("updated_at", 0) > 0 else None,
        )

    def list_all(self) -> List[dict]:
        """查询所有活跃任务（按创建时间升序）。"""
        stmt = select(ActiveTaskEntity).order_by(ActiveTaskEntity.created_at.asc())
        entities = self.session.execute(stmt).scalars().all()
        return [self._to_dto(e) for e in entities]

    def get_by_task_id(self, task_id: str) -> Optional[dict]:
        """
        根据任务 ID 查询。

        Args:
            task_id: 任务 ID

        Returns:
            任务字典，如果不存在则返回 None
        """
        entity = self.session.get(ActiveTaskEntity, task_id)
        return self._to_dto(entity) if entity else None

    def update_status(
        self,
        task_id: str,
        status: str,
        video_url: str = "",
    ) -> None:
        """
        更新任务状态。

        Args:
            task_id: 任务 ID
            status: 任务状态
            video_url: 视频 URL（可选）
        """
        entity = self.session.get(ActiveTaskEntity, task_id)
        if not entity:
            return

        entity.status = status
        if video_url:
            entity.video_url = video_url
        self.session.commit()

    def remove_task(self, task_id: str) -> bool:
        """
        移除任务。

        Args:
            task_id: 任务 ID

        Returns:
            是否移除成功
        """
        return self.delete(task_id)
