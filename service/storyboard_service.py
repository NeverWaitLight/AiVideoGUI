"""分镜头服务层：管理分镜 CRUD、历史版本、AI 生成。"""

from loguru import logger
import time

from models.enums import ShotSize
from models.storyboard import Storyboard, StoryboardHistory
from storage.session_manager import SessionManager
from storage.repositories.storyboard_repository import StoryboardRepository, StoryboardHistoryRepository
from utils.path_converter import to_relative_path

class StoryboardService:
    """分镜头业务逻辑服务。"""

    def __init__(self, session_mgr: SessionManager, workspace_root: str) -> None:
        self._session_mgr = session_mgr
        self._workspace_root = workspace_root

    # ---------- 分镜 CRUD ----------

    def list_storyboards(self, scene_id: int | None = None, project_id: int | None = None, scene_number: int | None = None) -> list[Storyboard]:
        """获取分镜列表。可按场次ID、项目ID或场次号过滤。"""
        repo = self._session_mgr.get_repo(StoryboardRepository)

        if scene_id is not None:
            return repo.list_by_scene(scene_id)
        elif project_id is not None:
            storyboards = repo.list_by_project(project_id)
            if scene_number is not None:
                return [s for s in storyboards if s.scene_number == scene_number]
            return storyboards
        else:
            # 无过滤条件，返回空列表
            return []

    def get_storyboard(self, storyboard_id: int) -> Storyboard | None:
        """获取单个分镜。"""
        repo = self._session_mgr.get_repo(StoryboardRepository)
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
    ) -> Storyboard:
        """创建新分镜。"""
        # 转换为相对路径存储
        relative_design_image = to_relative_path(design_image, self._workspace_root) if design_image else ""

        now_ms = int(time.time() * 1000)
        storyboard = Storyboard(
            id=0,  # 自增ID，数据库自动生成
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
            created_at=now_ms,
            updated_at=now_ms,
        )

        repo = self._session_mgr.get_repo(StoryboardRepository)
        self._session_mgr.begin_write()
        try:
            created = repo.create(storyboard)
            self._session_mgr.commit_write()
            logger.info(f"创建分镜：ID {created.id}，场次 {scene_number}-{shot_number}")
            return created
        except Exception:
            self._session_mgr.rollback_write()
            raise

    def batch_create_storyboards(self, storyboards: list[Storyboard]) -> None:
        """批量创建分镜（用于 AI 生成后导入）。"""
        repo = self._session_mgr.get_repo(StoryboardRepository)
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
    ) -> None:
        """更新分镜信息（历史版本自动保存由 ORM 监听器处理）。"""
        repo = self._session_mgr.get_repo(StoryboardRepository)

        self._session_mgr.begin_write()
        try:
            storyboard = repo.get_by_id(storyboard_id)
            if not storyboard:
                raise ValueError(f"分镜不存在：{storyboard_id}")

            # 更新字段（设计图需要转换为相对路径）
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

            storyboard.updated_at = int(time.time() * 1000)

            repo.update(storyboard)
            self._session_mgr.commit_write()
            logger.info(f"更新分镜：storyboard_id={storyboard_id}")
        except Exception:
            self._session_mgr.rollback_write()
            raise

    def delete_storyboard(self, storyboard_id: int) -> None:
        """删除分镜。"""
        repo = self._session_mgr.get_repo(StoryboardRepository)
        self._session_mgr.begin_write()
        try:
            repo.delete(storyboard_id)
            self._session_mgr.commit_write()
            logger.info(f"删除分镜：storyboard_id={storyboard_id}")
        except Exception:
            self._session_mgr.rollback_write()
            raise

    # ---------- 历史版本管理（自动保存由 ORM 监听器处理） ----------

    def list_history_timestamps(self, project_id: int) -> list[int]:
        """获取历史版本的时间戳列表（按时间倒序）。"""
        repo = self._session_mgr.get_repo(StoryboardHistoryRepository)
        return repo.distinct_timestamps_by_project(project_id)

    def list_history_by_timestamp(self, project_id: int, created_at: int) -> list[StoryboardHistory]:
        """获取指定时间戳的所有分镜历史。"""
        repo = self._session_mgr.get_repo(StoryboardHistoryRepository)
        return repo.list_by_project_and_timestamp(project_id, created_at)

    def restore_from_history(self, project_id: int, created_at: int) -> None:
        """从历史版本恢复分镜。"""
        storyboard_repo = self._session_mgr.get_repo(StoryboardRepository)
        history_repo = self._session_mgr.get_repo(StoryboardHistoryRepository)

        self._session_mgr.begin_write()
        try:
            # 按时间戳取出该次快照的所有分镜
            history_items = history_repo.list_by_project_and_timestamp(project_id, created_at)
            if not history_items:
                self._session_mgr.rollback_write()
                return

            # 删除当前所有分镜
            storyboard_repo.delete_by_project(project_id)

            # 恢复分镜
            now_ms = int(time.time() * 1000)
            for h in history_items:
                storyboard_repo.create(Storyboard(
                    id=0,  # 自增ID
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
