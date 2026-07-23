"""消息 Repository。"""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.data_models import Message, MessageStatus
from storage.orm.models import MessageEntity
from storage.repositories.base import BaseRepository


class MessageRepository(BaseRepository[MessageEntity, Message]):
    """消息 Repository。"""

    def __init__(self, session: Session):
        super().__init__(session, MessageEntity)

    def _to_dto(self, entity: MessageEntity) -> Message:
        """Entity → DTO 转换。"""
        return Message(
            id=entity.id,
            conversation_id=entity.conversation_id,
            role=entity.role,
            content=entity.content,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            task_id=entity.task_id,
            video_url=entity.video_url,
            local_path=entity.local_path,
            status=MessageStatus(entity.status),
            error_message=entity.error_message,
        )

    def _to_entity(self, dto: Message) -> MessageEntity:
        """DTO → Entity 转换。"""
        # 处理 status 字段：可能是枚举或字符串
        status_value = dto.status.value if isinstance(dto.status, MessageStatus) else dto.status

        if dto.id == 0:
            return MessageEntity(
                # 不设置 id，让数据库自动生成
                conversation_id=dto.conversation_id,
                role=dto.role,
                content=dto.content,
                created_at=dto.created_at if dto.created_at > 0 else None,
                updated_at=dto.updated_at if dto.updated_at > 0 else None,
                task_id=dto.task_id,
                video_url=dto.video_url,
                local_path=dto.local_path,
                status=status_value,
                error_message=dto.error_message,
            )
        else:
            return MessageEntity(
                id=dto.id,
                conversation_id=dto.conversation_id,
                role=dto.role,
                content=dto.content,
                created_at=dto.created_at,
                updated_at=dto.updated_at,
                task_id=dto.task_id,
                video_url=dto.video_url,
                local_path=dto.local_path,
                status=status_value,
                error_message=dto.error_message,
            )

    def list_by_conversation(self, conversation_id: int) -> List[Message]:
        """
        查询对话的所有消息（按时间升序）。

        Args:
            conversation_id: 对话 ID

        Returns:
            消息列表
        """
        stmt = (
            select(MessageEntity)
            .where(MessageEntity.conversation_id == conversation_id)
            .order_by(MessageEntity.created_at.asc())
        )
        entities = self.session.execute(stmt).scalars().all()
        return [self._to_dto(e) for e in entities]

    def update_status(
        self,
        message_id: int,
        status: MessageStatus,
        task_id: str = "",
        video_url: str = "",
        local_path: str = "",
        error_message: Optional[str] = None,
    ) -> None:
        """
        更新消息状态。

        Args:
            message_id: 消息 ID
            status: 消息状态
            task_id: 任务 ID（可选）
            video_url: 视频 URL（可选）
            local_path: 本地路径（可选）
            error_message: 错误消息（可选）
        """
        entity = self.session.get(MessageEntity, message_id)
        if not entity:
            return

        entity.status = status.value
        if task_id:
            entity.task_id = task_id
        if video_url:
            entity.video_url = video_url
        if local_path:
            entity.local_path = local_path
        if error_message is not None:
            entity.error_message = error_message
        self.session.commit()
