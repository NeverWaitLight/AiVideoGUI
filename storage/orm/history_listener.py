import time

from sqlalchemy import event, select

from storage.orm.character_entity import CharacterEntity, CharacterHistoryEntity
from storage.orm.screenplay_entity import ScreenplayEntity, ScreenplayHistoryEntity
from storage.orm.storyboard_entity import StoryboardEntity, StoryboardHistoryEntity
from storage.orm.story_outline_entity import StoryOutlineEntity, StoryOutlineHistoryEntity

_listeners_registered = False


def _save_story_outline_history(connection, target: StoryOutlineEntity):
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
            "content": target.content,
            "sound_effect": target.sound_effect,
            "ambient_sound": target.ambient_sound,
            "background_music": target.background_music,
            "duration": target.duration,
            "notes": target.notes,
            "created_at": int(time.time() * 1000),
        },
    )


def _save_character_history(connection, target: CharacterEntity):
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


def setup_history_listeners():
    global _listeners_registered

    if _listeners_registered:
        return

    @event.listens_for(StoryOutlineEntity, "after_insert", propagate=True)
    def on_story_outline_insert(mapper, connection, target: StoryOutlineEntity):
        _save_story_outline_history(connection, target)

    @event.listens_for(StoryOutlineEntity, "after_update", propagate=True)
    def on_story_outline_update(mapper, connection, target: StoryOutlineEntity):
        state = target._sa_instance_state
        if state.attrs.content.history.has_changes():
            _save_story_outline_history(connection, target)

    @event.listens_for(ScreenplayEntity, "after_insert", propagate=True)
    def on_screenplay_insert(mapper, connection, target: ScreenplayEntity):
        _save_screenplay_history(connection, target)

    @event.listens_for(ScreenplayEntity, "after_update", propagate=True)
    def on_screenplay_update(mapper, connection, target: ScreenplayEntity):
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

    @event.listens_for(StoryboardEntity, "after_insert", propagate=True)
    def on_storyboard_insert(mapper, connection, target: StoryboardEntity):
        _save_storyboard_history(connection, target)

    @event.listens_for(StoryboardEntity, "after_update", propagate=True)
    def on_storyboard_update(mapper, connection, target: StoryboardEntity):
        state = target._sa_instance_state
        key_fields_changed = any([
            state.attrs.shot_size.history.has_changes(),
            state.attrs.camera_movement.history.has_changes(),
            state.attrs.content.history.has_changes(),
            state.attrs.sound_effect.history.has_changes(),
            state.attrs.ambient_sound.history.has_changes(),
            state.attrs.background_music.history.has_changes(),
            state.attrs.duration.history.has_changes(),
            state.attrs.notes.history.has_changes(),
            state.attrs.design_image.history.has_changes(),
        ])
        if key_fields_changed:
            _save_storyboard_history(connection, target)

    @event.listens_for(CharacterEntity, "after_insert", propagate=True)
    def on_character_insert(mapper, connection, target: CharacterEntity):
        _save_character_history(connection, target)

    @event.listens_for(CharacterEntity, "after_update", propagate=True)
    def on_character_update(mapper, connection, target: CharacterEntity):
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
