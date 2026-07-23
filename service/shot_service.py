"""分镜头服务层：管理分镜 CRUD、历史版本、AI 生成。"""

import logging
import uuid
from datetime import datetime

from models.data_models import Shot, ShotHistory, ShotSize
from storage.database import DatabaseManager

logger = logging.getLogger(__name__)


class ShotService:
    """分镜头业务逻辑服务。"""

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    # ---------- 分镜 CRUD ----------

    def list_shots(self, scene_id: str | None = None, project_id: str | None = None, scene_number: int | None = None) -> list[Shot]:
        """获取分镜列表。可按场次ID、项目ID或场次号过滤。"""
        return self._db.list_shots(scene_id=scene_id, project_id=project_id, scene_number=scene_number)

    def get_shot(self, shot_id: str) -> Shot | None:
        """获取单个分镜。"""
        return self._db.get_shot(shot_id)

    def create_shot(
        self,
        scene_id: str,
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
    ) -> Shot:
        """创建新分镜。"""
        shot = Shot(
            id=str(uuid.uuid4()),
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
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        self._db.create_shot(shot)
        logger.info(f"创建分镜：scene_number={scene_number}, shot_number={shot_number}")
        return shot

    def batch_create_shots(self, shots: list[Shot]) -> None:
        """批量创建分镜（用于 AI 生成后导入）。"""
        self._db.batch_create_shots(shots)
        logger.info(f"批量创建 {len(shots)} 个分镜")

    def update_shot(
        self,
        shot_id: str,
        design_image: str | None = None,
        shot_size: ShotSize | None = None,
        camera_movement: str | None = None,
        visual_content: str | None = None,
        dialogue: str | None = None,
        sound_effect: str | None = None,
        duration: float | None = None,
        notes: str | None = None,
    ) -> None:
        """更新分镜信息。"""
        self._db.update_shot(
            shot_id=shot_id,
            design_image=design_image,
            shot_size=shot_size,
            camera_movement=camera_movement,
            visual_content=visual_content,
            dialogue=dialogue,
            sound_effect=sound_effect,
            duration=duration,
            notes=notes,
        )
        logger.info(f"更新分镜：shot_id={shot_id}")

    def delete_shot(self, shot_id: str) -> None:
        """删除分镜。"""
        self._db.delete_shot(shot_id)
        logger.info(f"删除分镜：shot_id={shot_id}")

    # ---------- 历史版本管理 ----------

    def save_history(self, project_id: str) -> None:
        """保存当前所有分镜到历史版本。"""
        shots = self._db.list_shots(project_id=project_id)
        if not shots:
            logger.warning(f"项目 {project_id} 没有分镜，无法保存历史")
            return
        self._db.create_shot_history(project_id, shots)
        logger.info(f"保存分镜历史：project_id={project_id}, 共 {len(shots)} 个分镜")

    def list_history(self, project_id: str) -> list[ShotHistory]:
        """获取历史版本列表。"""
        return self._db.list_shot_history(project_id)

    def restore_from_history(self, project_id: str, history_id: str) -> None:
        """从历史版本恢复分镜。"""
        self._db.restore_shots_from_history(project_id, history_id)
        logger.info(f"恢复分镜历史：project_id={project_id}, history_id={history_id}")
