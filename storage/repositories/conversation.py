"""对话 Repository。"""

from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.data_models import Conversation
from storage.orm.models import ConversationEntity
from storage.repositories.base import BaseRepository


class ConversationRepository(BaseRepository[ConversationEntity, Conversation]):
    """对话 Repository。"""

    def __init__(self, session: Session):
        super().__init__(session, ConversationEntity)

    def _to_dto(self, entity: ConversationEntity) -> Conversation:
        """Entity → DTO 转换。"""
        return Conversation(
            id=entity.id,
            title=entity.title,
            created_at=entity.created_at,
            model_name=entity.model_name,
            provider_name=entity.provider_name,
            project_id=entity.project_id,
            is_hidden=entity.is_hidden,
        )

    def _to_entity(self, dto: Conversation) -> ConversationEntity:
        """DTO → Entity 转换。"""
        return ConversationEntity(
            id=dto.id,
            title=dto.title,
            created_at=dto.created_at,
            model_name=dto.model_name,
            provider_name=dto.provider_name,
            project_id=dto.project_id,
            is_hidden=dto.is_hidden,
        )

    def list_all(self, is_hidden: bool = False) -> List[Conversation]:
        """
        查询所有对话（按创建时间倒序）。

        Args:
            is_hidden: 是否包含隐藏对话

        Returns:
            对话列表
        """
        stmt = (
            select(ConversationEntity)
            .where(ConversationEntity.is_hidden == is_hidden)
            .order_by(ConversationEntity.created_at.desc())
        )
        entities = self.session.execute(stmt).scalars().all()
        return [self._to_dto(e) for e in entities]

    def list_by_project(self, project_id: int, is_hidden: bool | None = None) -> List[Conversation]:
        """
        查询项目的所有对话。

        Args:
            project_id: 项目 ID
            is_hidden: 是否隐藏过滤（None=不过滤，True=仅隐藏，False=仅非隐藏）

        Returns:
            对话列表
        """
        stmt = (
            select(ConversationEntity)
            .where(ConversationEntity.project_id == project_id)
        )

        # 仅当 is_hidden 不为 None 时才添加过滤条件
        if is_hidden is not None:
            stmt = stmt.where(ConversationEntity.is_hidden == is_hidden)

        stmt = stmt.order_by(ConversationEntity.created_at.desc())
        entities = self.session.execute(stmt).scalars().all()
        return [self._to_dto(e) for e in entities]

    def update_title(self, conversation_id: str, title: str) -> None:
        """
        更新对话标题。

        Args:
            conversation_id: 对话 ID
            title: 新标题
        """
        entity = self.session.get(ConversationEntity, conversation_id)
        if not entity:
            return

        entity.title = title
        self.session.commit()

    def set_hidden(self, conversation_id: str, is_hidden: bool) -> None:
        """
        设置对话隐藏状态。

        Args:
            conversation_id: 对话 ID
            is_hidden: 是否隐藏
        """
        entity = self.session.get(ConversationEntity, conversation_id)
        if not entity:
            return

        entity.is_hidden = is_hidden
        self.session.commit()
