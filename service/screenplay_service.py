from __future__ import annotations

from loguru import logger
import time

from models.enums import SceneLocation, SceneTime
from models.scene import Scene, ScreenplayHistory
from storage.session_manager import SessionManager
from storage.repositories.screenplay_repository import ScreenplayRepository, ScreenplayHistoryRepository

class ScreenplayService:

    def __init__(self, session_manager: SessionManager) -> None:
        self._sm = session_manager

    def list_scenes(self, project_id: int) -> list[Scene]:
        screenplay_repo = self._sm.get_repo(ScreenplayRepository)
        return screenplay_repo.list_by_project(project_id)

    def get_scene(self, scene_id: int) -> Scene | None:
        screenplay_repo = self._sm.get_repo(ScreenplayRepository)
        return screenplay_repo.get_by_id(scene_id)

    def create_scene(
        self,
        project_id: int,
        scene_number: int,
        location_type: SceneLocation,
        location: str,
        time_type: SceneTime,
        time_detail: str,
        content: str,
    ) -> Scene:
        now_ms = int(time.time() * 1000)
        scene = Scene(
            id=0,
            project_id=project_id,
            scene_number=scene_number,
            location_type=location_type,
            location=location,
            time_type=time_type,
            time_detail=time_detail,
            content=content,
            created_at=now_ms,
            updated_at=now_ms,
        )

        screenplay_repo = self._sm.get_repo(ScreenplayRepository)
        self._sm.begin_write()
        try:
            created_scene = screenplay_repo.save(scene)
            self._sm.commit_write()
            logger.info(f"创建场次：ID {created_scene.id}，场次号：{scene_number}")
            return created_scene
        except Exception as e:
            self._sm.rollback_write()
            logger.error(f"创建场次失败: {e}")
            raise

    def update_scene(
        self,
        scene_id: int,
        location_type: SceneLocation | None = None,
        location: str | None = None,
        time_type: SceneTime | None = None,
        time_detail: str | None = None,
        content: str | None = None,
    ) -> None:
        screenplay_repo = self._sm.get_repo(ScreenplayRepository)

        scene = screenplay_repo.get_by_id(scene_id)
        if not scene:
            raise ValueError(f"场次不存在: {scene_id}")

        now_ms = int(time.time() * 1000)
        updated_scene = Scene(
            id=scene.id,
            project_id=scene.project_id,
            scene_number=scene.scene_number,
            location_type=location_type if location_type is not None else scene.location_type,
            location=location if location is not None else scene.location,
            time_type=time_type if time_type is not None else scene.time_type,
            time_detail=time_detail if time_detail is not None else scene.time_detail,
            content=content if content is not None else scene.content,
            created_at=scene.created_at,
            updated_at=now_ms,
        )

        self._sm.begin_write()
        try:
            screenplay_repo.save(updated_scene)
            self._sm.commit_write()
            logger.info(f"更新场次：{scene_id}")
        except Exception as e:
            self._sm.rollback_write()
            logger.error(f"更新场次失败: {e}")
            raise

    def delete_scene(self, scene_id: int) -> None:
        screenplay_repo = self._sm.get_repo(ScreenplayRepository)

        self._sm.begin_write()
        try:
            screenplay_repo.delete(scene_id)
            self._sm.commit_write()
            logger.info(f"删除场次：{scene_id}")
        except Exception as e:
            self._sm.rollback_write()
            logger.error(f"删除场次失败: {e}")
            raise

    def save_history(self, project_id: int) -> None:
        screenplay_repo = self._sm.get_repo(ScreenplayRepository)
        history_repo = self._sm.get_repo(ScreenplayHistoryRepository)

        scenes = screenplay_repo.list_by_project(project_id)

        self._sm.begin_write()
        try:
            now_ms = int(time.time() * 1000)
            for scene in scenes:
                history = ScreenplayHistory(
                    id=0,
                    screenplay_id=scene.id,
                    project_id=scene.project_id,
                    scene_number=scene.scene_number,
                    location_type=scene.location_type,
                    location=scene.location,
                    time_type=scene.time_type,
                    time_detail=scene.time_detail,
                    content=scene.content,
                    created_at=now_ms,
                )
                history_repo.save(history)

            self._sm.commit_write()
            logger.info(f"保存剧本历史：项目 {project_id}，共 {len(scenes)} 场")
        except Exception as e:
            self._sm.rollback_write()
            logger.error(f"保存剧本历史失败: {e}")
            raise

    def list_history_timestamps(self, project_id: int) -> list[int]:
        history_repo = self._sm.get_repo(ScreenplayHistoryRepository)
        return history_repo.distinct_timestamps_by_project(project_id)

    def list_history_by_timestamp(self, project_id: int, created_at: int) -> list[Scene]:
        history_repo = self._sm.get_repo(ScreenplayHistoryRepository)
        history_list = history_repo.list_by_project_and_timestamp(project_id, created_at)

        return [
            Scene(
                id=h.screenplay_id,
                project_id=h.project_id,
                scene_number=h.scene_number,
                location_type=h.location_type,
                location=h.location,
                time_type=h.time_type,
                time_detail=h.time_detail,
                content=h.content,
                created_at=h.created_at,
                updated_at=h.created_at,
            )
            for h in history_list
        ]

    def restore_from_history(self, project_id: int, created_at: int) -> None:
        screenplay_repo = self._sm.get_repo(ScreenplayRepository)
        history_repo = self._sm.get_repo(ScreenplayHistoryRepository)

        history_list = history_repo.list_by_project_and_timestamp(project_id, created_at)

        self._sm.begin_write()
        try:
            screenplay_repo.delete_by_project(project_id)

            now_ms = int(time.time() * 1000)
            for h in history_list:
                scene = Scene(
                    id=0,
                    project_id=h.project_id,
                    scene_number=h.scene_number,
                    location_type=h.location_type,
                    location=h.location,
                    time_type=h.time_type,
                    time_detail=h.time_detail,
                    content=h.content,
                    created_at=now_ms,
                    updated_at=now_ms,
                )
                screenplay_repo.save(scene)

            self._sm.commit_write()
            logger.info(f"恢复剧本历史版本：时间戳 {created_at}，共 {len(history_list)} 场")
        except Exception as e:
            self._sm.rollback_write()
            logger.error(f"恢复剧本历史版本失败: {e}")
            raise

    def batch_create_scenes(self, project_id: int, scenes_data: list[dict]) -> list[Scene]:
        screenplay_repo = self._sm.get_repo(ScreenplayRepository)
        now_ms = int(time.time() * 1000)

        created_scenes = []
        self._sm.begin_write()
        try:
            for data in scenes_data:
                location_type = data["location_type"]
                if isinstance(location_type, str):
                    location_type = SceneLocation(location_type)

                time_type = data["time_type"]
                if isinstance(time_type, str):
                    time_type = SceneTime(time_type)

                scene = Scene(
                    id=0,
                    project_id=project_id,
                    scene_number=data["scene_number"],
                    location_type=location_type,
                    location=data["location"],
                    time_type=time_type,
                    time_detail=data.get("time_detail", ""),
                    content=data["content"],
                    created_at=now_ms,
                    updated_at=now_ms,
                )
                created_scene = screenplay_repo.save(scene)
                created_scenes.append(created_scene)

            self._sm.commit_write()
            logger.info(f"批量创建场次完成：{len(created_scenes)} 场")
            return created_scenes
        except Exception as e:
            self._sm.rollback_write()
            logger.error(f"批量创建场次失败: {e}")
            raise
