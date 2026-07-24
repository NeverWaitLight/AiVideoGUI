"""ORM 历史版本自动保存监听器。

为所有拥有 history 表的实体注册 after_insert + after_update 事件，
在创建和关键字段变更时自动保存历史快照。
"""

import time

from sqlalchemy import event, select

from storage.orm.models import (
    CharacterEntity,
    CharacterHistoryEntity,
    ScreenplayEntity,
    ScreenplayHistoryEntity,
    StoryboardEntity,
    StoryboardHistoryEntity,
    StoryOutlineEntity,
    StoryOutlineHistoryEntity,
)

# 全局标志，防止重复注册
_listeners_registered = False


# ── 共用写入函数 ──────────────────────────────────────────────


def _save_story_outline_history(connection, target: StoryOutlineEntity):
    """将 StoryOutline 快照写入 story_outline_history。"""
    connection.execute(
        StoryOutlineHistoryEntity.__table__.insert(),
        {
            "story_outline_id": target.id,
            "project_id": target.project_id,
            "content": target.content,
            "created_at": int(time.time() * 1000),
        },
    )


def _save_screenplay_history(connection, target: ScreenplayEntity):
    """将 Screenplay 快照写入 screenplay_history。"""
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


def _save_storyboard_history(connection, target: StoryboardEntity):
    """将 Storyboard 快照写入 storyboard_history。"""
    result = connection.execute(
        select(ScreenplayEntity.project_id).where(
            ScreenplayEntity.id == target.scene_id
        )
    )
    project_id = result.scalar()
    if project_id is None:
        return

    connection.execute(
        StoryboardHistoryEntity.__table__.insert(),
        {
            "storyboard_id": target.id,
            "project_id": project_id,
            "scene_id": target.scene_id,
            "scene_number": target.scene_number,
            "shot_number": target.shot_number,
            "design_image": target.design_image,
            "shot_size": target.shot_size,
            "camera_movement": target.camera_movement,
            "visual_content": target.visual_content,
            "dialogue": target.dialogue,
            "sound_effect": target.sound_effect,
            "duration": target.duration,
            "notes": target.notes,
            "created_at": int(time.time() * 1000),
        },
    )


def _save_character_history(connection, target: CharacterEntity):
    """将 Character 快照写入 character_history（字段级快照）。"""
    connection.execute(
        CharacterHistoryEntity.__table__.insert(),
        {
            "character_id": target.uuid,
            "project_id": target.project_id,
            "name": target.name,
            "ref_code": target.ref_code,
            "design_image": target.design_image,
            "description": target.description,
            "created_at": int(time.time() * 1000),
        },
    )


# ── 监听器注册 ──────────────────────────────────────────────


def setup_history_listeners():
    """注册所有历史版本自动保存监听器（仅注册一次）。"""
    global _listeners_registered

    if _listeners_registered:
        return

    # ── StoryOutline ────────────────────────────────────────

    @event.listens_for(StoryOutlineEntity, "after_insert", propagate=True)
    def on_story_outline_insert(mapper, connection, target: StoryOutlineEntity):
        """StoryOutline 创建后自动保存初始快照。"""
        _save_story_outline_history(connection, target)

    @event.listens_for(StoryOutlineEntity, "after_update", propagate=True)
    def on_story_outline_update(mapper, connection, target: StoryOutlineEntity):
        """StoryOutline 更新后自动保存历史（仅 content 变化时）。"""
        state = target._sa_instance_state
        if state.attrs.content.history.has_changes():
            _save_story_outline_history(connection, target)

    # ── Screenplay ──────────────────────────────────────────

    @event.listens_for(ScreenplayEntity, "after_insert", propagate=True)
    def on_screenplay_insert(mapper, connection, target: ScreenplayEntity):
        """Screenplay 场次创建后自动保存初始快照。"""
        _save_screenplay_history(connection, target)

    @event.listens_for(ScreenplayEntity, "after_update", propagate=True)
    def on_screenplay_update(mapper, connection, target: ScreenplayEntity):
        """Screenplay 场次更新后自动保存历史（仅关键字段变化时）。"""
        state = target._sa_instance_state
        key_fields_changed = any([
            state.attrs.location_type.history.has_changes(),
            state.attrs.location.history.has_changes(),
            state.attrs.time_type.history.has_changes(),
            state.attrs.time_detail.history.has_changes(),
            state.attrs.content.history.has_changes(),
        ])
        if key_fields_changed:
            _save_screenplay_history(connection, target)

    # ── Storyboard ──────────────────────────────────────────

    @event.listens_for(StoryboardEntity, "after_insert", propagate=True)
    def on_storyboard_insert(mapper, connection, target: StoryboardEntity):
        """Storyboard 创建后自动保存初始快照。"""
        _save_storyboard_history(connection, target)

    @event.listens_for(StoryboardEntity, "after_update", propagate=True)
    def on_storyboard_update(mapper, connection, target: StoryboardEntity):
        """Storyboard 更新后自动保存历史（仅关键字段变化时）。"""
        state = target._sa_instance_state
        key_fields_changed = any([
            state.attrs.shot_size.history.has_changes(),
            state.attrs.camera_movement.history.has_changes(),
            state.attrs.visual_content.history.has_changes(),
            state.attrs.dialogue.history.has_changes(),
            state.attrs.sound_effect.history.has_changes(),
            state.attrs.duration.history.has_changes(),
            state.attrs.notes.history.has_changes(),
            state.attrs.design_image.history.has_changes(),
        ])
        if key_fields_changed:
            _save_storyboard_history(connection, target)

    # ── Character ───────────────────────────────────────────

    @event.listens_for(CharacterEntity, "after_insert", propagate=True)
    def on_character_insert(mapper, connection, target: CharacterEntity):
        """Character 创建后自动保存初始快照。"""
        _save_character_history(connection, target)

    @event.listens_for(CharacterEntity, "after_update", propagate=True)
    def on_character_update(mapper, connection, target: CharacterEntity):
        """Character 更新后自动保存历史（仅关键字段变化时）。"""
        state = target._sa_instance_state
        key_fields_changed = any([
            state.attrs.name.history.has_changes(),
            state.attrs.ref_code.history.has_changes(),
            state.attrs.description.history.has_changes(),
            state.attrs.design_image.history.has_changes(),
        ])
        if key_fields_changed:
            _save_character_history(connection, target)

    _listeners_registered = True
