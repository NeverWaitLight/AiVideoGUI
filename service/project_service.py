from __future__ import annotations

from loguru import logger
import os
import shutil
from datetime import datetime

from models.project import Project
from storage.session_manager import SessionManager
from storage.repositories.project_repository import ProjectRepository
from storage.repositories.media_repository import MediaRepository
from utils import paths

class ProjectService:

    def __init__(self, session_manager: SessionManager, workspace_root: str, take_service=None):
        self._sm = session_manager
        self._root = workspace_root
        self._take_service = take_service

    def create_project(self, name: str, resolution: str = "720P", aspect_ratio: str = "16:9", cover_image: str = "", visual_style_id: int | None = None) -> Project | None:
        project_repo = self._sm.get_repo(repo_class=ProjectRepository)

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
            visual_style_id=visual_style_id,
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
        project_repo = self._sm.get_repo(repo_class=ProjectRepository)
        return project_repo.list_all()

    def get_project(self, project_id: int) -> Project | None:
        project_repo = self._sm.get_repo(repo_class=ProjectRepository)
        return project_repo.get_by_id(project_id)

    def update_project(self, project_id: int, name: str, resolution: str, aspect_ratio: str, cover_image: str = "", visual_style_id: int | None = None) -> bool:
        project_repo = self._sm.get_repo(repo_class=ProjectRepository)

        if project_repo.exists_by_name(name=name, exclude_id=project_id):
            logger.warning(f"项目名称已存在：{name}")
            return False

        self._sm.begin_write()
        try:
            project_repo.update_project(project_id=project_id, name=name, resolution=resolution, aspect_ratio=aspect_ratio, cover_image=cover_image, visual_style_id=visual_style_id)
            self._sm.commit_write()
            return True
        except Exception as e:
            self._sm.rollback_write()
            logger.error(f"更新项目失败: {e}")
            raise

    def delete_project(self, project_id: int) -> None:
        project_repo = self._sm.get_repo(repo_class=ProjectRepository)

        self._sm.begin_write()
        try:
            if self._take_service:
                deleted = self._take_service.delete_by_project(project_id)
                if deleted:
                    logger.info(f"删除项目关联拍摄记录：project_id={project_id}, count={deleted}")

            entity = project_repo.session.get(project_repo.entity_class, project_id)
            if entity:
                project_repo.session.delete(entity)
            self._sm.commit_write()
        except Exception as e:
            self._sm.rollback_write()
            logger.error(f"删除项目数据失败: {e}")
            raise

        proj_dir = paths.project_dir(self._root, project_id)
        if os.path.isdir(proj_dir):
            try:
                shutil.rmtree(proj_dir)
            except OSError as e:
                logger.warning(f"删除项目目录失败 {proj_dir}: {e}")

    def update_cover_image(self, project_id: int, cover_image: str) -> bool:
        project_repo = self._sm.get_repo(repo_class=ProjectRepository)

        self._sm.begin_write()
        try:
            project = project_repo.get_by_id(project_id)
            if not project:
                logger.warning(f"项目不存在：project_id={project_id}")
                return False

            project_repo.update_project(
                project_id=project_id, name=project.name, resolution=project.resolution,
                aspect_ratio=project.aspect_ratio, cover_image=cover_image
            )
            self._sm.commit_write()
            return True
        except Exception as e:
            self._sm.rollback_write()
            logger.error(f"更新项目封面失败: {e}")
            raise
