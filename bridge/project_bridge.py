"""项目相关桥接：项目 CRUD 和导航。"""

from __future__ import annotations

import json
import os
import re
import shutil
from loguru import logger

from PySide6.QtCore import QObject, Property, Signal, Slot

from bridge.models.project_model import ProjectListModel
from bridge.models.conversation_model import ConversationListModel
from models.enums import MediaType
from storage.repositories.conversation_repository import ConversationRepository
from storage.repositories.media_repository import MediaRepository
from utils import paths


class ProjectBridge(QObject):
    """项目管理桥接。"""

    project_created = Signal(int)
    project_updated = Signal(int)
    project_deleted = Signal(int)

    def __init__(self, project_service, session_manager, parent=None):
        super().__init__(parent)
        self._project_service = project_service
        self._session_manager = session_manager
        self._grid_model = ProjectListModel(self)
        self._list_model = ProjectListModel(self)
        self._project_conversations = ConversationListModel(self)

    @Property(QObject, constant=True)
    def gridModel(self):
        return self._grid_model

    @Property(QObject, constant=True)
    def listModel(self):
        return self._list_model

    @Property(QObject, constant=True)
    def projectConversations(self):
        return self._project_conversations

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
        self._project_service.delete_project(project_id)
        # 清理项目目录
        project_dir = paths.projects_dir(paths.workspace_root())
        target = f"{project_dir}/{project_id}"
        if os.path.isdir(target):
            shutil.rmtree(target, ignore_errors=True)
        self.load_projects()
        self.project_deleted.emit(project_id)

    @Slot(int)
    def load_project_conversations(self, project_id: int) -> None:
        conv_repo = self._session_manager.get_repo(ConversationRepository)
        convs = conv_repo.list_by_project(project_id)
        self._project_conversations.reset(convs)

    @Slot(int, result=str)
    def get_project_info(self, project_id: int) -> str:
        """获取项目详情（JSON），包含名称、分辨率、宽高比、视频数、是否有分镜视频。"""
        project = self._project_service.get_project(project_id)
        if not project:
            return "{}"
        video_count = self._project_service.get_project_video_count(project_id)
        has_videos = self._has_storyboard_videos(project_id)
        return json.dumps({
            "name": project.name,
            "resolution": project.resolution,
            "aspectRatio": project.aspect_ratio,
            "coverImage": project.cover_image,
            "videoCount": video_count,
            "hasStoryboardVideos": has_videos,
        })

    def _has_storyboard_videos(self, project_id: int) -> bool:
        """判断项目是否有分镜视频（文件名匹配 场次-镜头-序号.mp4 格式）。"""
        conv_repo = self._session_manager.get_repo(ConversationRepository)
        conversations = conv_repo.list_by_project(project_id)
        conv_ids = {c.id for c in conversations}
        if not conv_ids:
            return False
        media_repo = self._session_manager.get_repo(MediaRepository)
        media_files = media_repo.list_with_filters(
            media_type=MediaType.VIDEO, conversation_ids=conv_ids,
        )
        pattern = re.compile(r"^\d+-\d+-\d+\.mp4$")
        return any(pattern.match(m.filename) for m in media_files)
