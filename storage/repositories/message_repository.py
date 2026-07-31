from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.enums import MessageStatus
from models.message import Message
from storage.orm.project_entity import MessageEntity
from storage.repositories.base_repository import BaseRepository
from utils.path_converter import to_absolute_path


class MessageRepository(BaseRepository[MessageEntity, Message]):

    def __init__(self, session: Session, workspace_root: str = ""):
        super().__init__(session, MessageEntity)
        self._workspace_root = workspace_root

    def _to_dto(self, entity: MessageEntity) -> Message:
        return Message(
            id=entity.id,
            conversation_id=entity.conversation_id,
            role=entity.role,
            content=entity.content,
            created_at=entity.created_at,
            task_id=entity.task_id,
            video_url=entity.video_url,
            local_path=to_absolute_path(entity.local_path, self._workspace_root),
            status=MessageStatus(entity.status),
            error_message=entity.error_message,
        )

    def _to_entity(self, dto: Message) -> MessageEntity:
        return MessageEntity(
            id=dto.id,
            conversation_id=dto.conversation_id,
            role=dto.role,
            content=dto.content,
            created_at=dto.created_at,
            task_id=dto.task_id,
            video_url=dto.video_url,
            local_path=dto.local_path,
            status=dto.status.value,
            error_message=dto.error_message,
        )

    def list_by_conversation(self, conversation_id: str) -> List[Message]:
        stmt = (
            select(MessageEntity)
            .where(MessageEntity.conversation_id == conversation_id)
            .order_by(MessageEntity.created_at.asc())
        )
        entities = self.session.execute(stmt).scalars().all()
        return [self._to_dto(e) for e in entities]

    def update_status(
        self,
        message_id: str,
        status: MessageStatus,
        task_id: str = "",
        video_url: str = "",
        local_path: str = "",
        error_message: Optional[str] = None,
    ) -> None:
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
