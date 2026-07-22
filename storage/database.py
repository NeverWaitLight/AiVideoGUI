"""SQLite 数据库管理（SQLAlchemy ORM 版本）。"""

import json
import logging
import threading
from datetime import datetime
from typing import Optional

from models.data_models import (
    Conversation,
    MediaFile,
    MediaType,
    Message,
    MessageStatus,
    Outline,
    OutlineHistory,
    Scene,
    Script,
    ScriptHistory,
    Shot,
    ShotHistory,
)
from storage.orm.base import create_all_tables, get_session, init_engine
from storage.repositories.active_task import ActiveTaskRepository
from storage.repositories.conversation import ConversationRepository
from storage.repositories.media import MediaRepository
from storage.repositories.message import MessageRepository
from storage.repositories.outline import OutlineHistoryRepository, OutlineRepository
from storage.repositories.project import ProjectRepository
from storage.repositories.script import SceneRepository, ScriptHistoryRepository, ScriptRepository
from storage.repositories.shot import ShotHistoryRepository, ShotRepository

logger = logging.getLogger(__name__)


class DatabaseManager:
    """SQLite 数据库管理（SQLAlchemy ORM 适配器）。"""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._lock = threading.RLock()

        # 初始化 SQLAlchemy
        database_url = f"sqlite:///{db_path}"
        init_engine(database_url, echo=False)

        # 创建所有表（如果不存在）
        create_all_tables()

        logger.info("数据库初始化完成（SQLAlchemy ORM）：%s", db_path)

    def _get_session(self):
        """获取当前线程的 Session。"""
        return get_session()

    # ========== Conversation 相关方法 ==========

    def create_conversation(self, conv: Conversation) -> None:
        """创建对话。"""
        with self._lock:
            session = self._get_session()
            repo = ConversationRepository(session)
            repo.create(conv)

    def get_conversation(self, conversation_id: str) -> Conversation | None:
        """根据 ID 查询单个对话。"""
        session = self._get_session()
        repo = ConversationRepository(session)
        return repo.get_by_id(conversation_id)

    def list_conversations(self) -> list[Conversation]:
        """查询所有对话（不包含隐藏对话）。"""
        session = self._get_session()
        repo = ConversationRepository(session)
        return repo.list_all(is_hidden=False)

    def delete_conversation(self, conversation_id: str) -> None:
        """删除对话。"""
        with self._lock:
            session = self._get_session()
            repo = ConversationRepository(session)
            repo.delete(conversation_id)

    def update_conversation_title(self, conversation_id: str, title: str) -> None:
        """更新对话标题。"""
        with self._lock:
            session = self._get_session()
            repo = ConversationRepository(session)
            repo.update_title(conversation_id, title)

    def list_project_conversations(self, project_id: str) -> list[Conversation]:
        """查询项目的所有对话。"""
        session = self._get_session()
        repo = ConversationRepository(session)
        return repo.list_by_project(project_id, is_hidden=False)

    # ========== Message 相关方法 ==========

    def add_message(self, msg: Message) -> None:
        """添加消息。"""
        with self._lock:
            session = self._get_session()
            repo = MessageRepository(session)
            repo.create(msg)

    def get_message(self, message_id: str) -> Message | None:
        """根据 ID 查询消息。"""
        session = self._get_session()
        repo = MessageRepository(session)
        return repo.get_by_id(message_id)

    def list_messages(self, conversation_id: str) -> list[Message]:
        """查询对话的所有消息。"""
        session = self._get_session()
        repo = MessageRepository(session)
        return repo.list_by_conversation(conversation_id)

    def update_message_status(
        self,
        message_id: str,
        status: MessageStatus,
        task_id: str = "",
        video_url: str = "",
        local_path: str = "",
        error_message: str = "",
    ) -> None:
        """更新消息状态。"""
        with self._lock:
            session = self._get_session()
            repo = MessageRepository(session)
            repo.update_status(
                message_id=message_id,
                status=status,
                task_id=task_id,
                video_url=video_url,
                local_path=local_path,
                error_message=error_message or None,
            )

    # ========== ActiveTask 相关方法 ==========

    def add_active_task(
        self,
        task_id: str,
        message_id: str,
        provider_name: str,
        model_name: str,
        save_path: str = "",
        video_url: str = "",
        status: str = "pending",
    ) -> None:
        """添加活跃任务。"""
        with self._lock:
            session = self._get_session()
            repo = ActiveTaskRepository(session)
            repo.create({
                "task_id": task_id,
                "message_id": message_id,
                "provider_name": provider_name,
                "model_name": model_name,
                "video_url": video_url,
                "status": status,
                "save_path": save_path,
                "created_at": datetime.now(),
            })

    def list_active_tasks(self) -> list[dict]:
        """查询所有活跃任务。"""
        session = self._get_session()
        repo = ActiveTaskRepository(session)
        return repo.list_all()

    def update_active_task(self, task_id: str, status: str, video_url: str = "") -> None:
        """更新任务状态。"""
        with self._lock:
            session = self._get_session()
            repo = ActiveTaskRepository(session)
            repo.update_status(task_id, status, video_url)

    def remove_active_task(self, task_id: str) -> None:
        """移除活跃任务。"""
        with self._lock:
            session = self._get_session()
            repo = ActiveTaskRepository(session)
            repo.remove_task(task_id)

    def get_next_storyboard_seq(self, scene_number: int, shot_number: int) -> int:
        """
        获取下一个分镜序号（场次号 * 1000 + 镜头号）。

        Args:
            scene_number: 场次号
            shot_number: 镜头号

        Returns:
            分镜序号
        """
        return scene_number * 1000 + shot_number

    # ========== MediaFile 相关方法 ==========

    def add_media_file(self, media: MediaFile) -> None:
        """添加素材文件。"""
        with self._lock:
            session = self._get_session()
            repo = MediaRepository(session)
            repo.create(media)

    def list_media_files(
        self,
        media_type: Optional[MediaType | str] = None,
        keyword: Optional[str] = None,
        project_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> list[MediaFile]:
        """
        查询素材文件。

        Args:
            media_type: 素材类型过滤（MediaType 枚举或字符串）
            keyword: 关键词过滤（文件名）
            project_id: 项目 ID 过滤（通过对话关联）
            conversation_id: 对话 ID 过滤

        Returns:
            素材文件列表
        """
        session = self._get_session()
        repo = MediaRepository(session)

        # 转换字符串为 MediaType 枚举（处理 UI 层传入的字符串）
        if isinstance(media_type, str):
            media_type = MediaType(media_type)

        files = repo.list_all(media_type)

        # 应用过滤条件
        if conversation_id:
            files = [f for f in files if f.conversation_id == conversation_id]

        if keyword:
            files = [f for f in files if keyword.lower() in f.filename.lower()]

        if project_id:
            conv_repo = ConversationRepository(session)
            project_convs = conv_repo.list_by_project(project_id)
            conv_ids = {c.id for c in project_convs}
            files = [f for f in files if f.conversation_id in conv_ids]

        return files

    def delete_media_file(self, media_id: str) -> MediaFile | None:
        """
        删除素材文件。

        Args:
            media_id: 素材 ID

        Returns:
            被删除的素材文件，如果不存在则返回 None
        """
        with self._lock:
            session = self._get_session()
            repo = MediaRepository(session)
            media = repo.get_by_id(media_id)
            if media:
                repo.delete(media_id)
            return media

    def get_media_file_by_message(self, message_id: str) -> MediaFile | None:
        """
        根据消息 ID 查询素材文件。

        Args:
            message_id: 消息 ID

        Returns:
            素材文件，如果不存在则返回 None
        """
        session = self._get_session()
        repo = MediaRepository(session)
        files = repo.list_all()
        for f in files:
            if f.message_id == message_id:
                return f
        return None

    def get_video_metadata_by_message(self, message_id: str) -> dict | None:
        """
        根据消息 ID 查询视频元数据。

        Args:
            message_id: 消息 ID

        Returns:
            元数据字典，如果不存在则返回 None
        """
        media = self.get_media_file_by_message(message_id)
        if media:
            return {
                "thumbnail_path": media.thumbnail_path,
                "duration": media.duration,
                "width": media.width,
                "height": media.height,
            }
        return None

    # ========== Project 相关方法 ==========

    def create_project(
        self,
        project_id: str,
        name: str,
        resolution: str,
        aspect_ratio: str,
        cover_image: str = "",
    ) -> None:
        """创建项目。"""
        with self._lock:
            session = self._get_session()
            repo = ProjectRepository(session)
            from models.data_models import Project

            repo.create(Project(
                id=project_id,
                name=name,
                resolution=resolution,
                aspect_ratio=aspect_ratio,
                created_at=datetime.now(),
                cover_image=cover_image,
            ))

    def list_projects(self) -> list[dict]:
        """查询所有项目（返回字典格式以保持兼容性）。"""
        session = self._get_session()
        repo = ProjectRepository(session)
        projects = repo.list_all()
        return [
            {
                "id": p.id,
                "name": p.name,
                "resolution": p.resolution,
                "aspect_ratio": p.aspect_ratio,
                "created_at": p.created_at,
                "cover_image": p.cover_image,
            }
            for p in projects
        ]

    def get_project(self, project_id: str) -> dict | None:
        """查询项目。"""
        session = self._get_session()
        repo = ProjectRepository(session)
        project = repo.get_by_id(project_id)
        if project:
            return {
                "id": project.id,
                "name": project.name,
                "resolution": project.resolution,
                "aspect_ratio": project.aspect_ratio,
                "created_at": project.created_at,
                "cover_image": project.cover_image,
            }
        return None

    def update_project(
        self,
        project_id: str,
        name: str,
        resolution: str,
        aspect_ratio: str,
        cover_image: str = "",
    ) -> None:
        """更新项目。"""
        with self._lock:
            session = self._get_session()
            repo = ProjectRepository(session)
            repo.update_project(project_id, name, resolution, aspect_ratio, cover_image)

    def delete_project(self, project_id: str) -> None:
        """删除项目。"""
        with self._lock:
            session = self._get_session()
            repo = ProjectRepository(session)
            repo.delete(project_id)

    # ========== Outline 相关方法 ==========

    def get_outline(self, project_id: str) -> Outline | None:
        """查询项目的大纲。"""
        session = self._get_session()
        repo = OutlineRepository(session)
        return repo.get_by_project(project_id)

    def create_outline(self, outline: Outline) -> None:
        """创建大纲。"""
        with self._lock:
            session = self._get_session()
            repo = OutlineRepository(session)
            repo.create(outline)

    def update_outline(self, outline_id: str, content: str) -> None:
        """更新大纲内容。"""
        with self._lock:
            session = self._get_session()
            repo = OutlineRepository(session)
            repo.update_content(outline_id, content, datetime.now())

            # 自动保存历史版本
            history_repo = OutlineHistoryRepository(session)
            import uuid

            history_repo.create(OutlineHistory(
                id=str(uuid.uuid4()),
                outline_id=outline_id,
                content=content,
                created_at=datetime.now(),
            ))

    def list_outline_history(self, outline_id: str) -> list[OutlineHistory]:
        """查询大纲的所有历史版本。"""
        session = self._get_session()
        repo = OutlineHistoryRepository(session)
        return repo.list_by_outline(outline_id)

    def restore_outline_from_history(self, outline_id: str, history_id: str) -> None:
        """从历史版本恢复大纲。"""
        with self._lock:
            session = self._get_session()
            history_repo = OutlineHistoryRepository(session)
            history = history_repo.get_by_id(history_id)

            if history:
                outline_repo = OutlineRepository(session)
                outline_repo.update_content(outline_id, history.content, datetime.now())

    # ========== Script 相关方法 ==========

    def get_script(self, project_id: str) -> Script | None:
        """查询项目的剧本。"""
        session = self._get_session()
        repo = ScriptRepository(session)
        return repo.get_by_project(project_id)

    def create_script(self, script: Script) -> None:
        """创建剧本。"""
        with self._lock:
            session = self._get_session()
            repo = ScriptRepository(session)
            repo.create(script)

    def update_script(self, script_id: str, title: str) -> None:
        """更新剧本标题。"""
        with self._lock:
            session = self._get_session()
            repo = ScriptRepository(session)
            repo.update_script(script_id, title, datetime.now())

    def list_scenes(self, script_id: str) -> list[Scene]:
        """查询剧本的所有场次。"""
        session = self._get_session()
        repo = SceneRepository(session)
        return repo.list_by_script(script_id)

    def get_scene(self, scene_id: str) -> Scene | None:
        """查询场次。"""
        session = self._get_session()
        repo = SceneRepository(session)
        return repo.get_by_id(scene_id)

    def create_scene(self, scene: Scene) -> None:
        """创建场次。"""
        with self._lock:
            session = self._get_session()
            repo = SceneRepository(session)
            repo.create(scene)

    def update_scene(
        self,
        scene_id: str,
        location_type: str | None = None,
        location: str | None = None,
        time_type: str | None = None,
        time_detail: str | None = None,
        content: str | None = None,
        scene_number: int | None = None,
    ) -> None:
        """更新场次。"""
        with self._lock:
            session = self._get_session()
            from storage.orm.models import SceneEntity

            entity = session.get(SceneEntity, scene_id)
            if entity:
                if scene_number is not None:
                    entity.scene_number = scene_number
                if location_type is not None:
                    entity.location_type = location_type
                if location is not None:
                    entity.location = location
                if time_type is not None:
                    entity.time_type = time_type
                if time_detail is not None:
                    entity.time_detail = time_detail
                if content is not None:
                    entity.content = content
                entity.updated_at = datetime.now()
                session.commit()

    def delete_scene(self, scene_id: str) -> None:
        """删除场次。"""
        with self._lock:
            session = self._get_session()
            repo = SceneRepository(session)
            repo.delete(scene_id)

    def create_script_history(self, script_id: str, title: str, scenes: list[Scene]) -> None:
        """创建剧本历史快照。"""
        with self._lock:
            session = self._get_session()
            repo = ScriptHistoryRepository(session)
            import uuid

            # 将 scenes 序列化为 JSON
            scenes_data = [
                {
                    "scene_number": s.scene_number,
                    "location_type": s.location_type.value if hasattr(s.location_type, "value") else s.location_type,
                    "location": s.location,
                    "time_type": s.time_type.value if hasattr(s.time_type, "value") else s.time_type,
                    "time_detail": s.time_detail,
                    "content": s.content,
                }
                for s in scenes
            ]

            repo.create(ScriptHistory(
                id=str(uuid.uuid4()),
                script_id=script_id,
                title=title,
                scenes_snapshot=json.dumps(scenes_data, ensure_ascii=False),
                created_at=datetime.now(),
            ))

    def list_script_history(self, script_id: str) -> list[ScriptHistory]:
        """查询剧本的所有历史版本。"""
        session = self._get_session()
        repo = ScriptHistoryRepository(session)
        return repo.list_by_script(script_id)

    def restore_script_from_history(self, script_id: str, history_id: str) -> None:
        """从历史版本恢复剧本。"""
        with self._lock:
            session = self._get_session()
            history_repo = ScriptHistoryRepository(session)
            history = history_repo.get_by_id(history_id)

            if not history:
                return

            # 删除当前所有场次
            scene_repo = SceneRepository(session)
            scene_repo.delete_by_script(script_id)

            # 恢复场次
            scenes_data = json.loads(history.scenes_snapshot)
            import uuid

            for scene_data in scenes_data:
                scene_repo.create(Scene(
                    id=str(uuid.uuid4()),
                    script_id=script_id,
                    scene_number=scene_data["scene_number"],
                    location_type=scene_data["location_type"],
                    location=scene_data["location"],
                    time_type=scene_data["time_type"],
                    time_detail=scene_data.get("time_detail", ""),
                    content=scene_data.get("content", ""),
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                ))

            # 更新剧本标题
            script_repo = ScriptRepository(session)
            script_repo.update_script(script_id, history.title, datetime.now())

    # ========== Shot 相关方法 ==========

    def list_shots(
        self,
        scene_id: str | None = None,
        project_id: str | None = None,
        scene_number: int | None = None,
    ) -> list[Shot]:
        """
        查询分镜。

        Args:
            scene_id: 场次 ID（优先级最高）
            project_id: 项目 ID
            scene_number: 场次号（需配合 project_id 使用）

        Returns:
            分镜列表
        """
        session = self._get_session()
        repo = ShotRepository(session)

        if scene_id:
            return repo.list_by_scene(scene_id)
        elif project_id:
            shots = repo.list_by_project(project_id)
            if scene_number is not None:
                shots = [s for s in shots if s.scene_number == scene_number]
            return shots
        else:
            return []

    def get_shot(self, shot_id: str) -> Shot | None:
        """查询分镜。"""
        session = self._get_session()
        repo = ShotRepository(session)
        return repo.get_by_id(shot_id)

    def create_shot(self, shot: Shot) -> None:
        """创建分镜。"""
        with self._lock:
            session = self._get_session()
            repo = ShotRepository(session)
            repo.create(shot)

    def batch_create_shots(self, shots: list[Shot]) -> None:
        """批量创建分镜。"""
        with self._lock:
            session = self._get_session()
            repo = ShotRepository(session)
            for shot in shots:
                repo.create(shot)

    def update_shot(
        self,
        shot_id: str,
        design_image: str | None = None,
        shot_size: str | None = None,
        camera_movement: str | None = None,
        visual_content: str | None = None,
        dialogue: str | None = None,
        sound_effect: str | None = None,
        duration: float | None = None,
        notes: str | None = None,
        scene_number: int | None = None,
        shot_number: int | None = None,
    ) -> None:
        """更新分镜。"""
        with self._lock:
            session = self._get_session()
            from storage.orm.models import ShotEntity

            entity = session.get(ShotEntity, shot_id)
            if entity:
                if scene_number is not None:
                    entity.scene_number = scene_number
                if shot_number is not None:
                    entity.shot_number = shot_number
                if design_image is not None:
                    entity.design_image = design_image
                if shot_size is not None:
                    entity.shot_size = shot_size
                if camera_movement is not None:
                    entity.camera_movement = camera_movement
                if visual_content is not None:
                    entity.visual_content = visual_content
                if dialogue is not None:
                    entity.dialogue = dialogue
                if sound_effect is not None:
                    entity.sound_effect = sound_effect
                if duration is not None:
                    entity.duration = duration
                if notes is not None:
                    entity.notes = notes
                entity.updated_at = datetime.now()
                session.commit()

    def delete_shot(self, shot_id: str) -> None:
        """删除分镜。"""
        with self._lock:
            session = self._get_session()
            repo = ShotRepository(session)
            repo.delete(shot_id)

    def create_shot_history(self, project_id: str, shots: list[Shot]) -> None:
        """创建分镜历史快照。"""
        with self._lock:
            session = self._get_session()
            repo = ShotHistoryRepository(session)
            import uuid

            # 将 shots 序列化为 JSON
            shots_data = [
                {
                    "scene_number": s.scene_number,
                    "shot_number": s.shot_number,
                    "design_image": s.design_image,
                    "shot_size": s.shot_size,
                    "camera_movement": s.camera_movement,
                    "visual_content": s.visual_content,
                    "dialogue": s.dialogue,
                    "sound_effect": s.sound_effect,
                    "duration": s.duration,
                    "notes": s.notes,
                }
                for s in shots
            ]

            repo.create(ShotHistory(
                id=str(uuid.uuid4()),
                project_id=project_id,
                shots_snapshot=json.dumps(shots_data, ensure_ascii=False),
                created_at=datetime.now(),
            ))

    def list_shot_history(self, project_id: str) -> list[ShotHistory]:
        """查询项目的所有分镜历史版本。"""
        session = self._get_session()
        repo = ShotHistoryRepository(session)
        return repo.list_by_project(project_id)

    def restore_shots_from_history(self, project_id: str, history_id: str) -> None:
        """从历史版本恢复分镜。"""
        with self._lock:
            session = self._get_session()
            history_repo = ShotHistoryRepository(session)
            history = history_repo.get_by_id(history_id)

            if not history:
                return

            # 删除当前所有分镜
            shot_repo = ShotRepository(session)
            current_shots = shot_repo.list_by_project(project_id)
            for shot in current_shots:
                shot_repo.delete(shot.id)

            # 获取项目的剧本和场次
            script_repo = ScriptRepository(session)
            script = script_repo.get_by_project(project_id)
            if not script:
                return

            scene_repo = SceneRepository(session)
            scenes = scene_repo.list_by_script(script.id)
            scene_map = {s.scene_number: s.id for s in scenes}

            # 恢复分镜
            shots_data = json.loads(history.shots_snapshot)
            import uuid

            for shot_data in shots_data:
                scene_number = shot_data["scene_number"]
                scene_id = scene_map.get(scene_number)
                if not scene_id:
                    continue

                shot_repo.create(Shot(
                    id=str(uuid.uuid4()),
                    scene_id=scene_id,
                    scene_number=shot_data["scene_number"],
                    shot_number=shot_data["shot_number"],
                    design_image=shot_data.get("design_image", ""),
                    shot_size=shot_data.get("shot_size", "medium_shot"),
                    camera_movement=shot_data.get("camera_movement", ""),
                    visual_content=shot_data.get("visual_content", ""),
                    dialogue=shot_data.get("dialogue", ""),
                    sound_effect=shot_data.get("sound_effect", ""),
                    duration=shot_data.get("duration", 0.0),
                    notes=shot_data.get("notes", ""),
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                ))

    # ========== 其他方法 ==========

    def close(self) -> None:
        """关闭数据库连接。"""
        from storage.orm.base import close_session

        close_session()
        logger.info("数据库连接已关闭")

