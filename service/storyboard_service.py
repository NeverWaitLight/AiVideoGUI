from loguru import logger
import time

from models.enums import ShotSize
from models.storyboard import Storyboard, StoryboardHistory
from storage.session_manager import SessionManager
from storage.repositories.storyboard_repository import StoryboardRepository, StoryboardHistoryRepository
from utils.path_converter import to_relative_path

class StoryboardService:

    def __init__(self, session_mgr: SessionManager, workspace_root: str) -> None:
        self._session_mgr = session_mgr
        self._workspace_root = workspace_root

    def list_storyboards(self, scene_id: int | None = None, project_id: int | None = None, scene_number: int | None = None) -> list[Storyboard]:
        repo = self._session_mgr.get_repo(repo_class=StoryboardRepository)

        if scene_id is not None:
            return repo.list_by_scene(scene_id)
        elif project_id is not None:
            storyboards = repo.list_by_project(project_id)
            if scene_number is not None:
                return [s for s in storyboards if s.scene_number == scene_number]
            return storyboards
        else:
            return []

    def get_storyboard(self, storyboard_id: int) -> Storyboard | None:
        repo = self._session_mgr.get_repo(repo_class=StoryboardRepository)
        return repo.get_by_id(storyboard_id)

    def create_storyboard(
        self,
        scene_id: int,
        scene_number: int,
        shot_number: int,
        shot_size: ShotSize = ShotSize.MEDIUM_SHOT,
        camera_movement: str = "",
        visual_content: str = "",
        dialogue: str = "",
        sound_effect: str = "",
        duration: float = 0.0,
        notes: str = "",
        design_image: str = "",
        seed: str = "",
    ) -> Storyboard:
        relative_design_image = to_relative_path(design_image, self._workspace_root) if design_image else ""

        now_ms = int(time.time() * 1000)
        storyboard = Storyboard(
            id=0,
            scene_id=scene_id,
            scene_number=scene_number,
            shot_number=shot_number,
            design_image=relative_design_image,
            shot_size=shot_size,
            camera_movement=camera_movement,
            visual_content=visual_content,
            dialogue=dialogue,
            sound_effect=sound_effect,
            duration=duration,
            notes=notes,
            seed=seed,
            created_at=now_ms,
            updated_at=now_ms,
        )

        repo = self._session_mgr.get_repo(repo_class=StoryboardRepository)
        self._session_mgr.begin_write()
        try:
            created = repo.create(storyboard=storyboard)
            self._session_mgr.commit_write()
            logger.info(f"创建分镜：ID {created.id}，场次 {scene_number}-{shot_number}")
            return created
        except Exception:
            self._session_mgr.rollback_write()
            raise

    def batch_create_storyboards(self, storyboards: list[Storyboard]) -> None:
        repo = self._session_mgr.get_repo(repo_class=StoryboardRepository)
        self._session_mgr.begin_write()
        try:
            for storyboard in storyboards:
                repo.create(storyboard)
            self._session_mgr.commit_write()
            logger.info(f"批量创建 {len(storyboards)} 个分镜")
        except Exception:
            self._session_mgr.rollback_write()
            raise

    def update_storyboard(
        self,
        storyboard_id: int,
        design_image: str | None = None,
        shot_size: ShotSize | None = None,
        camera_movement: str | None = None,
        visual_content: str | None = None,
        dialogue: str | None = None,
        sound_effect: str | None = None,
        duration: float | None = None,
        notes: str | None = None,
        seed: str | None = None,
    ) -> None:
        repo = self._session_mgr.get_repo(repo_class=StoryboardRepository)

        self._session_mgr.begin_write()
        try:
            storyboard = repo.get_by_id(storyboard_id)
            if not storyboard:
                raise ValueError(f"分镜不存在：{storyboard_id}")

            if design_image is not None:
                storyboard.design_image = to_relative_path(design_image, self._workspace_root) if design_image else ""
            if shot_size is not None:
                storyboard.shot_size = shot_size
            if camera_movement is not None:
                storyboard.camera_movement = camera_movement
            if visual_content is not None:
                storyboard.visual_content = visual_content
            if dialogue is not None:
                storyboard.dialogue = dialogue
            if sound_effect is not None:
                storyboard.sound_effect = sound_effect
            if duration is not None:
                storyboard.duration = duration
            if notes is not None:
                storyboard.notes = notes
            if seed is not None:
                storyboard.seed = seed

            storyboard.updated_at = int(time.time() * 1000)

            repo.update(storyboard=storyboard)
            self._session_mgr.commit_write()
            logger.info(f"更新分镜：storyboard_id={storyboard_id}")
        except Exception:
            self._session_mgr.rollback_write()
            raise

    def delete_storyboard(self, storyboard_id: int) -> None:
        repo = self._session_mgr.get_repo(repo_class=StoryboardRepository)
        self._session_mgr.begin_write()
        try:
            repo.delete(storyboard_id=storyboard_id)
            self._session_mgr.commit_write()
            logger.info(f"删除分镜：storyboard_id={storyboard_id}")
        except Exception:
            self._session_mgr.rollback_write()
            raise

    def list_history_timestamps(self, project_id: int) -> list[int]:
        repo = self._session_mgr.get_repo(repo_class=StoryboardHistoryRepository)
        return repo.distinct_timestamps_by_project(project_id)

    def list_history_by_timestamp(self, project_id: int, created_at: int) -> list[StoryboardHistory]:
        repo = self._session_mgr.get_repo(repo_class=StoryboardHistoryRepository)
        return repo.list_by_project_and_timestamp(project_id, created_at)

    def restore_from_history(self, project_id: int, created_at: int) -> None:
        storyboard_repo = self._session_mgr.get_repo(StoryboardRepository)
        history_repo = self._session_mgr.get_repo(StoryboardHistoryRepository)

        self._session_mgr.begin_write()
        try:
            history_items = history_repo.list_by_project_and_timestamp(project_id=project_id, created_at=created_at)
            if not history_items:
                self._session_mgr.rollback_write()
                return

            storyboard_repo.delete_by_project(project_id=project_id)

            now_ms = int(time.time() * 1000)
            for h in history_items:
                storyboard_repo.create(Storyboard(
                    id=0,
                    scene_id=h.scene_id,
                    scene_number=h.scene_number,
                    shot_number=h.shot_number,
                    design_image=h.design_image,
                    shot_size=h.shot_size,
                    camera_movement=h.camera_movement,
                    visual_content=h.visual_content,
                    dialogue=h.dialogue,
                    sound_effect=h.sound_effect,
                    duration=h.duration,
                    notes=h.notes,
                    created_at=now_ms,
                    updated_at=now_ms,
                ))

            self._session_mgr.commit_write()
            logger.info(f"恢复分镜历史：project_id={project_id}, created_at={created_at}")
        except Exception:
            self._session_mgr.rollback_write()
            raise
