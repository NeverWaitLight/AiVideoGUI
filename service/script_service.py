"""剧本服务：管理场次的 CRUD 操作。"""

from __future__ import annotations

import logging
import time

from models.data_models import ScriptHistory, Scene, SceneLocation, SceneTime
from storage.database import DatabaseManager

logger = logging.getLogger(__name__)


class ScriptService:
    """剧本服务：支持场次管理（scripts 表现在就是场次表）。"""

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    def list_scenes(self, project_id: int) -> list[Scene]:
        """获取项目的所有场次。"""
        return self._db.list_scenes(project_id)

    def get_scene(self, scene_id: int) -> Scene | None:
        """获取单个场次。"""
        return self._db.get_scene(scene_id)

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
        """创建场次。"""
        now_ms = int(time.time() * 1000)
        scene = Scene(
            id=0,  # 自增ID，数据库自动生成
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
        created_scene = self._db.create_scene(scene)
        logger.info(f"创建场次：ID {created_scene.id}，场次号：{scene_number}")
        return created_scene

    def update_scene(
        self,
        scene_id: int,
        location_type: SceneLocation | None = None,
        location: str | None = None,
        time_type: SceneTime | None = None,
        time_detail: str | None = None,
        content: str | None = None,
    ) -> None:
        """更新场次信息。"""
        self._db.update_scene(
            scene_id,
            location_type=location_type.value if location_type else None,
            location=location,
            time_type=time_type.value if time_type else None,
            time_detail=time_detail,
            content=content,
        )
        logger.info(f"更新场次：{scene_id}")

    def delete_scene(self, scene_id: int) -> None:
        """删除场次。"""
        self._db.delete_scene(scene_id)
        logger.info(f"删除场次：{scene_id}")

    def save_history(self, project_id: int) -> None:
        """保存剧本历史版本（快照所有场次）。"""
        scenes = self._db.list_scenes(project_id)
        self._db.create_script_history(project_id, scenes)
        logger.info(f"保存剧本历史：项目 {project_id}，共 {len(scenes)} 场")

    def list_history(self, project_id: int) -> list[ScriptHistory]:
        """获取剧本历史版本列表。"""
        return self._db.list_script_history(project_id)

    def restore_from_history(self, project_id: int, history_id: int) -> None:
        """从历史版本恢复剧本。"""
        self._db.restore_script_from_history(project_id, history_id)
        logger.info(f"恢复剧本历史版本：{history_id}")

    def batch_create_scenes(self, project_id: int, scenes_data: list[dict]) -> list[Scene]:
        """批量创建场次（用于 AI 生成剧本）。

        Args:
            project_id: 项目 ID
            scenes_data: 场次数据列表，每个元素包含：
                - scene_number: 场次号
                - location_type: 内外景类型（SceneLocation 枚举值或字符串）
                - location: 地点
                - time_type: 时间类型（SceneTime 枚举值或字符串）
                - time_detail: 详细时间（可选）
                - content: 场次内容

        Returns:
            创建的场次列表
        """
        created_scenes = []
        for data in scenes_data:
            # 转换枚举类型
            location_type = data["location_type"]
            if isinstance(location_type, str):
                location_type = SceneLocation(location_type)

            time_type = data["time_type"]
            if isinstance(time_type, str):
                time_type = SceneTime(time_type)

            scene = self.create_scene(
                project_id=project_id,
                scene_number=data["scene_number"],
                location_type=location_type,
                location=data["location"],
                time_type=time_type,
                time_detail=data.get("time_detail", ""),
                content=data["content"],
            )
            created_scenes.append(scene)

        logger.info(f"批量创建场次完成：{len(created_scenes)} 场")
        return created_scenes
