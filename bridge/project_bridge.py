from __future__ import annotations

import json
import os
import re
import shutil
from loguru import logger

from PySide6.QtCore import QObject, Property, Signal, Slot

from bridge.models.project_model import ProjectListModel
from models.enums import MediaType
from storage.repositories.media_repository import MediaRepository
from utils import paths


class ProjectBridge(QObject):
    project_created = Signal(int)
    project_updated = Signal(int)
    project_deleted = Signal(int)
    cover_generation_started = Signal()
    cover_generation_finished = Signal(str)
    cover_generation_failed = Signal(str)

    def __init__(self, project_service, session_manager, parent=None):
        super().__init__(parent)
        self._project_service = project_service
        self._session_manager = session_manager
        self._grid_model = ProjectListModel(self)
        self._list_model = ProjectListModel(self)
        self._workspace_root = None

    @Property(QObject, constant=True)
    def gridModel(self):
        return self._grid_model

    @Property(QObject, constant=True)
    def listModel(self):
        return self._list_model

    @Slot()
    def load_projects(self) -> None:
        projects = self._project_service.list_projects()
        self._grid_model.reset(projects)
        self._list_model.reset(projects)

    @Slot(str, str, str, str)
    def create_project(self, name: str, resolution: str, ratio: str, cover: str) -> None:
        project = self._project_service.create_project(
            name=name, resolution=resolution, aspect_ratio=ratio, cover_image=cover,
        )
        if project:
            self.load_projects()
            self.project_created.emit(project.id)

    @Slot(str, result=int)
    def create_project_default(self, name: str) -> int:
        project = self._project_service.create_project(
            name=name, resolution="720P", aspect_ratio="16:9", cover_image="",
        )
        if project:
            self.load_projects()
            self.project_created.emit(project.id)
            return project.id
        return -1

    @Slot(int, str, str, str, str)
    def update_project(self, project_id: int, name: str, resolution: str,
                       ratio: str, cover: str) -> None:
        self._project_service.update_project(
            project_id=project_id, name=name, resolution=resolution,
            aspect_ratio=ratio, cover_image=cover,
        )
        self.load_projects()
        self.project_updated.emit(project_id)

    @Slot(int)
    def delete_project(self, project_id: int) -> None:
        self._project_service.delete_project(project_id=project_id)
        project_dir = paths.projects_dir(paths.workspace_root())
        target = f"{project_dir}/{project_id}"
        if os.path.isdir(target):
            shutil.rmtree(target, ignore_errors=True)
        self.load_projects()
        self.project_deleted.emit(project_id)

    @Slot(int, result=str)
    def get_project_info(self, project_id: int) -> str:
        project = self._project_service.get_project(project_id=project_id)
        if not project:
            return "{}"
        has_videos = self._has_storyboard_videos(project_id)
        cover_abs = ""
        if project.cover_image and self._workspace_root:
            workspace_dir = paths.workspace_dir(self._workspace_root)
            cover_abs = os.path.join(workspace_dir, project.cover_image).replace("\\", "/")
        return json.dumps({
            "name": project.name,
            "resolution": project.resolution,
            "aspectRatio": project.aspect_ratio,
            "coverImage": project.cover_image or "",
            "coverImagePath": cover_abs,
            "videoCount": 0,
            "hasStoryboardVideos": has_videos,
        })

    def _has_storyboard_videos(self, project_id: int) -> bool:
        media_repo = self._session_manager.get_repo(repo_class=MediaRepository)
        media_files = media_repo.list_with_filters(
            media_type=MediaType.VIDEO, conversation_ids=None,
        )
        pattern = re.compile(r"^\d+-\d+-\d+\.mp4$")
        return any(pattern.match(m.filename) for m in media_files)

    def set_workspace_root(self, workspace_root: str):
        self._workspace_root = workspace_root

    @Slot(int, str, str, str, str, str, str)
    def generate_cover_with_character(
        self, project_id: int, character_name: str, appearance: str,
        aspect_ratio: str, project_name: str, outline_content: str, design_image_path: str
    ) -> None:
        logger.info("封面图生成功能已禁用")
        self.cover_generation_failed.emit("封面图生成功能暂不可用")

    @Slot(str, result=str)
    def resolve_cover_path(self, absolute_path: str) -> str:
        if not absolute_path or not self._workspace_root:
            return absolute_path
        workspace_dir = paths.workspace_dir(self._workspace_root)
        try:
            return os.path.relpath(absolute_path, workspace_dir).replace("\\", "/")
        except ValueError:
            return absolute_path

