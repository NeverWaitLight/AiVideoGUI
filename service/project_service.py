from __future__ import annotations

from loguru import logger
import os
import shutil
from datetime import datetime

from models.conversation import Conversation
from models.project import Project
from storage.session_manager import SessionManager
from storage.repositories.project_repository import ProjectRepository
from storage.repositories.conversation_repository import ConversationRepository
from storage.repositories.message_repository import MessageRepository
from storage.repositories.media_repository import MediaRepository
from utils import paths

class ProjectService:

    def __init__(self, session_manager: SessionManager, workspace_root: str):
        self._sm = session_manager
        self._root = workspace_root

    def create_project(self, name: str, resolution: str = "720P", aspect_ratio: str = "16:9", cover_image: str = "") -> Project | None:
        project_repo = self._sm.get_repo(ProjectRepository)

        if project_repo.exists_by_name(name):
            logger.warning(f"项目名称已存在：{name}")
            return None

        now_ts = int(datetime.now().timestamp() * 1000)
        project = Project(
            id=0,
            name=name,
            resolution=resolution,
            aspect_ratio=aspect_ratio,
            created_at=now_ts,
            updated_at=now_ts,
            cover_image=cover_image,
        )

        self._sm.begin_write()
        try:
            saved_project = project_repo.save(project)
            self._sm.commit_write()

            proj_dir = paths.project_dir(self._root, saved_project.id)
            os.makedirs(proj_dir, exist_ok=True)

            return saved_project
        except Exception as e:
            self._sm.rollback_write()
            logger.error(f"创建项目失败: {e}")
            raise

    def list_projects(self) -> list[Project]:
        project_repo = self._sm.get_repo(ProjectRepository)
        return project_repo.list_all()

    def get_project(self, project_id: int) -> Project | None:
        project_repo = self._sm.get_repo(ProjectRepository)
        return project_repo.get_by_id(project_id)

    def update_project(self, project_id: int, name: str, resolution: str, aspect_ratio: str, cover_image: str = "") -> bool:
        project_repo = self._sm.get_repo(ProjectRepository)

        if project_repo.exists_by_name(name, exclude_id=project_id):
            logger.warning(f"项目名称已存在：{name}")
            return False

        self._sm.begin_write()
        try:
            project_repo.update_project(project_id, name, resolution, aspect_ratio, cover_image)
            self._sm.commit_write()
            return True
        except Exception as e:
            self._sm.rollback_write()
            logger.error(f"更新项目失败: {e}")
            raise

    def delete_project(self, project_id: int) -> None:
        logger.info(f"开始删除项目：project_id={project_id}")

        conv_repo = self._sm.get_repo(ConversationRepository)
        media_repo = self._sm.get_repo(MediaRepository)
        project_repo = self._sm.get_repo(ProjectRepository)

        self._sm.begin_write()
        try:
            project_convs = conv_repo.list_by_project(project_id)
            conv_ids = {c.id for c in project_convs}

            all_media_files = media_repo.list_all()
            project_media_files = [f for f in all_media_files if f.conversation_id in conv_ids]

            logger.info(f"找到 {len(project_media_files)} 个项目关联的素材文件")
            for media in project_media_files:
                media_repo.delete(media.id)

            project_repo.delete(project_id)

            self._sm.commit_write()
        except Exception as e:
            self._sm.rollback_write()
            logger.error(f"删除项目数据失败: {e}")
            raise

        proj_dir = paths.project_dir(self._root, project_id)
        if os.path.isdir(proj_dir):
            try:
                shutil.rmtree(proj_dir)
                logger.info(f"已删除项目目录：{proj_dir}")
            except OSError as e:
                logger.warning(f"删除项目目录失败 {proj_dir}: {e}")

        logger.info(f"项目删除完成：project_id={project_id}")

    def list_project_conversations(self, project_id: int) -> list[Conversation]:
        conv_repo = self._sm.get_repo(ConversationRepository)
        return conv_repo.list_by_project(project_id)

    def get_project_video_count(self, project_id: int) -> int:
        conv_repo = self._sm.get_repo(ConversationRepository)
        msg_repo = self._sm.get_repo(MessageRepository)

        convs = conv_repo.list_by_project(project_id)
        count = 0
        for conv in convs:
            messages = msg_repo.list_by_conversation(conv.id)
            count += sum(1 for msg in messages if msg.role == "assistant" and msg.local_path)
        return count
