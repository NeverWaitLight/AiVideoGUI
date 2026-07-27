"""分镜头服务层：管理分镜 CRUD、历史版本、AI 生成。"""

import logging
import time

from models.data_models import Storyboard, StoryboardHistory, ShotSize
from storage.database import DatabaseManager

logger = logging.getLogger(__name__)


class StoryboardService:
    """分镜头业务逻辑服务。"""

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    # ---------- 分镜 CRUD ----------

    def list_storyboards(self, scene_id: str | None = None, project_id: int | None = None, scene_number: int | None = None) -> list[Storyboard]:
        """获取分镜列表。可按场次ID、项目ID或场次号过滤。"""
        return self._db.list_storyboards(scene_id=scene_id, project_id=project_id, scene_number=scene_number)

    def get_storyboard(self, storyboard_id: int) -> Storyboard | None:
        """获取单个分镜。"""
        return self._db.get_storyboard(storyboard_id)

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
        now_ms = int(time.time() * 1000)
        storyboard = Storyboard(
            scene_id=scene_id,
            scene_number=scene_number,
            shot_number=shot_number,
            design_image=design_image,
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
        return self._db.create_storyboard(storyboard)

    def batch_create_storyboards(self, storyboards: list[Storyboard]) -> None:
        """批量创建分镜（用于 AI 生成后导入）。"""
        self._db.batch_create_storyboards(storyboards)
        logger.info(f"批量创建 {len(storyboards)} 个分镜")

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
        self._db.update_storyboard(
            storyboard_id=storyboard_id,
            design_image=design_image,
            shot_size=shot_size,
            camera_movement=camera_movement,
            visual_content=visual_content,
            dialogue=dialogue,
            sound_effect=sound_effect,
            duration=duration,
            notes=notes,
        )
        logger.info(f"更新分镜：storyboard_id={storyboard_id}")

    def delete_storyboard(self, storyboard_id: int) -> None:
        """删除分镜。"""
        self._db.delete_storyboard(storyboard_id)
        logger.info(f"删除分镜：storyboard_id={storyboard_id}")

    # ---------- 历史版本管理（自动保存由 ORM 监听器处理） ----------

    def list_history_timestamps(self, project_id: int) -> list[int]:
        """获取历史版本的时间戳列表（按时间倒序）。"""
        return self._db.list_storyboard_history_timestamps(project_id)

    def list_history_by_timestamp(self, project_id: int, created_at: int) -> list[StoryboardHistory]:
        """获取指定时间戳的所有分镜历史。"""
        return self._db.list_storyboard_history_by_timestamp(project_id, created_at)

    def restore_from_history(self, project_id: int, created_at: int) -> None:
        """从历史版本恢复分镜。"""
        self._db.restore_storyboards_from_history(project_id, created_at)
        logger.info(f"恢复分镜历史：project_id={project_id}, created_at={created_at}")
