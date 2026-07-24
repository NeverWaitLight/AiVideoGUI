"""剧本服务：管理剧本和场次的 CRUD 操作。"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime

from models.data_models import Script, ScriptHistory, Scene, SceneLocation, SceneTime
from storage.database import DatabaseManager

logger = logging.getLogger(__name__)


class ScriptService:
    """剧本服务：支持剧本和场次管理。"""

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    def get_or_create_script(self, project_id: int) -> Script:
        """获取或创建项目剧本。"""
        script = self._db.get_script(project_id)
        if script:
            return script

        # 创建新剧本
        now = datetime.now()
        script = Script(
            id=str(uuid.uuid4()),
            project_id=project_id,
            title="",
            created_at=now,
            updated_at=now,
        )
        self._db.create_script(script)
        logger.info(f"创建新剧本：{script.id}")
        return script

    def get_script_by_project(self, project_id: int) -> Script | None:
        """根据项目ID获取剧本。"""
        return self._db.get_script(project_id)

    def update_script_title(self, script_id: str, title: str) -> None:
        """更新剧本标题。"""
        self._db.update_script(script_id, title)
        logger.info(f"更新剧本标题：{script_id}")

    def list_scenes(self, script_id: str) -> list[Scene]:
        """获取剧本的所有场次。"""
        return self._db.list_scenes(script_id)

    def get_scene(self, scene_id: str) -> Scene | None:
        """获取单个场次。"""
        return self._db.get_scene(scene_id)

    def create_scene(
        self,
        script_id: str,
        scene_number: int,
        location_type: SceneLocation,
        location: str,
        time_type: SceneTime,
        time_detail: str,
        content: str,
    ) -> Scene:
        """创建场次。"""
        now = datetime.now()
        scene = Scene(
            id=str(uuid.uuid4()),
            script_id=script_id,
            scene_number=scene_number,
            location_type=location_type,
            location=location,
            time_type=time_type,
            time_detail=time_detail,
            content=content,
            created_at=now,
            updated_at=now,
        )
        self._db.create_scene(scene)
        logger.info(f"创建场次：{scene.id}，场次号：{scene_number}")
        return scene

    def update_scene(
        self,
        scene_id: str,
        location_type: SceneLocation | None = None,
        location: str | None = None,
        time_type: SceneTime | None = None,
        time_detail: str | None = None,
        content: str | None = None,
    ) -> None:
        """更新场次信息。"""
        self._db.update_scene(
            scene_id,
            location_type=location_type,
            location=location,
            time_type=time_type,
            time_detail=time_detail,
            content=content,
        )
        logger.info(f"更新场次：{scene_id}")

    def delete_scene(self, scene_id: str) -> None:
        """删除场次。"""
        self._db.delete_scene(scene_id)
        logger.info(f"删除场次：{scene_id}")

    def save_history(self, script_id: str, title: str) -> None:
        """保存剧本历史版本（快照所有场次）。"""
        scenes = self._db.list_scenes(script_id)
        self._db.create_script_history(script_id, title, scenes)
        logger.info(f"保存剧本历史：{script_id}，共 {len(scenes)} 场")

    def list_history(self, script_id: str) -> list[ScriptHistory]:
        """获取剧本历史版本列表。"""
        return self._db.list_script_history(script_id)

    def restore_from_history(self, script_id: str, history_id: str) -> None:
        """从历史版本恢复剧本。"""
        self._db.restore_script_from_history(script_id, history_id)
        logger.info(f"恢复剧本历史版本：{history_id}")

    def batch_create_scenes(self, script_id: str, scenes_data: list[dict]) -> list[Scene]:
        """批量创建场次（用于 AI 生成剧本）。

        Args:
            script_id: 剧本 ID
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
                script_id=script_id,
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
