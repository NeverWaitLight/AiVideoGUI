"""ORM 历史版本自动保存监听器。"""

import time
import uuid
from datetime import datetime

from sqlalchemy import event
from sqlalchemy.orm import Session

from storage.orm.models import (
    CharacterEntity,
    CharacterHistoryEntity,
    ScreenplayEntity,
    ScreenplayHistoryEntity,
    StoryOutlineEntity,
    StoryOutlineHistoryEntity,
)

# 全局标志，防止重复注册
_listeners_registered = False


def setup_history_listeners():
    """注册所有历史版本自动保存监听器（仅注册一次）。"""
    global _listeners_registered

    if _listeners_registered:
        return

    # StoryOutline 更新时自动保存历史
    @event.listens_for(StoryOutlineEntity, "after_update", propagate=True)
    def on_story_outline_update(mapper, connection, target: StoryOutlineEntity):
        """
        StoryOutline 更新后自动保存到 story_outline_history。

        注意：只在 content 字段变化时保存历史版本，避免 updated_at 更新触发重复保存。
        """
        # 获取 Session 来检查哪些字段被修改
        state = target._sa_instance_state
        history = state.attrs.content.history

        # 只有 content 字段有变化时才保存历史
        if history.has_changes():
            # 不设置 id 字段，让数据库自动生成自增ID
            connection.execute(
                StoryOutlineHistoryEntity.__table__.insert(),
                {
                    "story_outline_id": target.id,
                    "project_id": target.project_id,
                    "content": target.content,
                    "created_at": int(time.time() * 1000),
                },
            )

    # Screenplay 更新时自动保存历史
    @event.listens_for(ScreenplayEntity, "after_update", propagate=True)
    def on_screenplay_update(mapper, connection, target: ScreenplayEntity):
        """
        Screenplay 场次更新后自动保存到 screenplay_history。

        注意：只在关键字段变化时保存，避免 updated_at 更新触发重复保存。
        """
        state = target._sa_instance_state

        key_fields_changed = any([
            state.attrs.location_type.history.has_changes(),
            state.attrs.location.history.has_changes(),
            state.attrs.time_type.history.has_changes(),
            state.attrs.time_detail.history.has_changes(),
            state.attrs.content.history.has_changes(),
        ])

        if key_fields_changed:
            connection.execute(
                ScreenplayHistoryEntity.__table__.insert(),
                {
                    "screenplay_id": target.id,
                    "project_id": target.project_id,
                    "scene_number": target.scene_number,
                    "location_type": target.location_type,
                    "location": target.location,
                    "time_type": target.time_type,
                    "time_detail": target.time_detail,
                    "content": target.content,
                    "created_at": int(time.time() * 1000),
                },
            )

    # Character 更新时自动保存历史
    @event.listens_for(CharacterEntity, "after_update", propagate=True)
    def on_character_update(mapper, connection, target: CharacterEntity):
        """
        Character 更新后自动保存到 character_history。

        注意：只在关键字段变化时保存历史版本。
        """
        import json

        state = target._sa_instance_state

        # 检查是否有关键字段变化（name, ref_code, description, design_image）
        key_fields_changed = any([
            state.attrs.name.history.has_changes(),
            state.attrs.ref_code.history.has_changes(),
            state.attrs.description.history.has_changes(),
            state.attrs.design_image.history.has_changes(),
        ])

        if key_fields_changed:
            snapshot = json.dumps({
                "name": target.name,
                "ref_code": target.ref_code,
                "description": target.description,
                "design_image": target.design_image,
            }, ensure_ascii=False)

            connection.execute(
                CharacterHistoryEntity.__table__.insert(),
                {
                    "id": str(uuid.uuid4()),
                    "character_id": target.uuid,
                    "snapshot": snapshot,
                    "created_at": datetime.now(),
                },
            )

    _listeners_registered = True


