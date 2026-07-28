"""项目服务：管理项目 CRUD 和对话关联。"""

from __future__ import annotations

from loguru import logger
import os
import shutil
from datetime import datetime

from models.conversation import Conversation
from models.project import Project
from storage.session_manager import SessionManager
from storage.repositories.project import ProjectRepository
from storage.repositories.conversation import ConversationRepository
from storage.repositories.message import MessageRepository
from storage.repositories.media import MediaRepository
from utils import paths

class ProjectService:
    """项目服务类。"""

    def __init__(self, session_manager: SessionManager, workspace_root: str):
        self._sm = session_manager
        self._root = workspace_root

    def create_project(self, name: str, resolution: str = "720P", aspect_ratio: str = "16:9", cover_image: str = "") -> Project | None:
        """
        创建新项目。

        Args:
            name: 项目名称
            resolution: 分辨率
            aspect_ratio: 宽高比
            cover_image: 封面图路径

        Returns:
            创建的项目对象，如果名称重复则返回 None
        """
        project_repo = self._sm.get_repo(ProjectRepository)

        # 检查名称是否已存在
        if project_repo.exists_by_name(name):
            logger.warning(f"项目名称已存在：{name}")
            return None

        now_ts = int(datetime.now().timestamp() * 1000)
        project = Project(
            id=0,  # 自增主键，创建时为 0
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

            # 预创建项目目录
            proj_dir = paths.project_dir(self._root, saved_project.id)
            os.makedirs(proj_dir, exist_ok=True)

            return saved_project
        except Exception as e:
            self._sm.rollback_write()
            logger.error(f"创建项目失败: {e}")
            raise

    def list_projects(self) -> list[Project]:
        """列出所有项目。"""
        project_repo = self._sm.get_repo(ProjectRepository)
        return project_repo.list_all()

    def get_project(self, project_id: int) -> Project | None:
        """获取单个项目。"""
        project_repo = self._sm.get_repo(ProjectRepository)
        return project_repo.get_by_id(project_id)

    def update_project(self, project_id: int, name: str, resolution: str, aspect_ratio: str, cover_image: str = "") -> bool:
        """
        更新项目信息。

        Args:
            project_id: 项目 ID
            name: 项目名称
            resolution: 分辨率
            aspect_ratio: 宽高比
            cover_image: 封面图路径

        Returns:
            True 表示更新成功，False 表示名称重复
        """
        project_repo = self._sm.get_repo(ProjectRepository)

        # 检查名称是否与其他项目重复
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
        """删除项目（级联删除所有关联数据和文件）。"""
        logger.info(f"开始删除项目：project_id={project_id}")

        conv_repo = self._sm.get_repo(ConversationRepository)
        media_repo = self._sm.get_repo(MediaRepository)
        project_repo = self._sm.get_repo(ProjectRepository)

        self._sm.begin_write()
        try:
            # 1. 查询项目关联的所有素材文件（通过对话关联），删除数据库记录
            project_convs = conv_repo.list_by_project(project_id)
            conv_ids = {c.id for c in project_convs}

            all_media_files = media_repo.list_all()
            project_media_files = [f for f in all_media_files if f.conversation_id in conv_ids]

            logger.info(f"找到 {len(project_media_files)} 个项目关联的素材文件")
            for media in project_media_files:
                media_repo.delete(media.id)

            # 2. 数据库级联删除会自动处理：
            #    - story_outlines (ON DELETE CASCADE)
            #    - story_outline_history (ON DELETE CASCADE)
            #    - screenplay (ON DELETE CASCADE)
            #    - screenplay_history (ON DELETE CASCADE)
            #    - storyboard (ON DELETE CASCADE)
            #    - storyboard_history (ON DELETE CASCADE)

            # 3. 删除项目（会清除对话的 project_id 关联）
            project_repo.delete(project_id)

            self._sm.commit_write()
        except Exception as e:
            self._sm.rollback_write()
            logger.error(f"删除项目数据失败: {e}")
            raise

        # 4. 删除项目目录（包含所有视频、缩略图等文件）
        proj_dir = paths.project_dir(self._root, project_id)
        if os.path.isdir(proj_dir):
            try:
                shutil.rmtree(proj_dir)
                logger.info(f"已删除项目目录：{proj_dir}")
            except OSError as e:
                logger.warning(f"删除项目目录失败 {proj_dir}: {e}")

        logger.info(f"项目删除完成：project_id={project_id}")

    def list_project_conversations(self, project_id: int) -> list[Conversation]:
        """列出项目下的所有对话。"""
        conv_repo = self._sm.get_repo(ConversationRepository)
        return conv_repo.list_by_project(project_id)

    def get_project_video_count(self, project_id: int) -> int:
        """获取项目下的视频总数。"""
        conv_repo = self._sm.get_repo(ConversationRepository)
        msg_repo = self._sm.get_repo(MessageRepository)

        convs = conv_repo.list_by_project(project_id)
        count = 0
        for conv in convs:
            messages = msg_repo.list_by_conversation(conv.id)
            count += sum(1 for msg in messages if msg.role == "assistant" and msg.local_path)
        return count
