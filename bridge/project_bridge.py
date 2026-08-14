from __future__ import annotations

import json
import os
import re
import shutil

from PySide6.QtCore import QObject, Property, Signal, Slot, QThread

from bridge.models.project_model import ProjectListModel
from bridge.workers import CoverGenerationWorker
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

    def __init__(self, project_service, session_manager, visual_style_service, chat_model_service, image_service,
                 container=None, parent=None):
        super().__init__(parent)
        self._project_service = project_service
        self._session_manager = session_manager
        self._visual_style_service = visual_style_service
        self._chat_model_service = chat_model_service
        self._image_service = image_service
        self._container = container
        self._grid_model = ProjectListModel(visual_style_service, self)
        self._list_model = ProjectListModel(visual_style_service, self)
        self._workspace_root = None
        self._cover_worker = None
        self._cover_thread = None

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

    @Slot(str, str, str, str, int)
    def create_project(self, name: str, resolution: str, ratio: str, cover: str, visual_style_id: int) -> None:
        style_id = None if visual_style_id <= 0 else visual_style_id
        project = self._project_service.create_project(
            name=name, resolution=resolution, aspect_ratio=ratio, cover_image=cover, visual_style_id=style_id,
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

    @Slot(int, str, str, str, str, int)
    def update_project(self, project_id: int, name: str, resolution: str,
                       ratio: str, cover: str, visual_style_id: int) -> None:
        style_id = None if visual_style_id <= 0 else visual_style_id
        self._project_service.update_project(
            project_id=project_id, name=name, resolution=resolution,
            aspect_ratio=ratio, cover_image=cover, visual_style_id=style_id,
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
            "visualStyleId": project.visual_style_id if project.visual_style_id is not None else -1,
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

    @Slot(result=str)
    def list_projects_for_filter(self) -> str:
        try:
            projects = self._project_service.list_projects()
            return json.dumps([
                {"id": p.id, "name": p.name}
                for p in projects
            ])
        except Exception as e:
            return "[]"

    @Slot(int, str, str, str, str, str, str)
    def generate_cover_with_characters(
        self, project_id: int, character_names: str, appearances: str,
        aspect_ratio: str, project_name: str, outline_content: str, design_image_paths: str
    ) -> None:
        """
        生成项目封面图（支持多个角色）

        Args:
            project_id: 项目 ID
            character_names: 角色名称，多个用 ", " 分隔
            appearances: 角色描述，多个用 "\n\n" 分隔
            aspect_ratio: 画面比例
            project_name: 项目名称
            outline_content: 大纲内容
            design_image_paths: 设计图路径，多个用 "|" 分隔
        """
        if self._cover_worker and self._cover_thread and self._cover_thread.isRunning():
            return

        project = self._project_service.get_project(project_id=project_id)
        if not project:
            self.cover_generation_failed.emit("项目不存在")
            return

        visual_style = ""
        if project.visual_style_id:
            style = self._visual_style_service.get_style(project.visual_style_id)
            if style:
                visual_style = style.name

        self._cover_thread = QThread()
        self._cover_worker = CoverGenerationWorker(
            project_id=project_id,
            project_name=project_name,
            aspect_ratio=aspect_ratio,
            outline_content=outline_content,
            character_names=character_names,
            appearances=appearances,
            design_image_paths=design_image_paths,
            visual_style=visual_style,
            image_service=self._image_service,
            project_service=self._project_service,
            workspace_root=self._workspace_root,
            config_manager=self._container.config_manager() if self._container else None,
            session_manager=self._container.session_manager() if self._container else None,
        )
        self._cover_worker.moveToThread(self._cover_thread)

        self._cover_thread.started.connect(self._cover_worker.run)
        self._cover_worker.finished.connect(self._on_cover_finished)
        self._cover_worker.failed.connect(self._on_cover_failed)
        self._cover_worker.finished.connect(self._cover_thread.quit)
        self._cover_worker.failed.connect(self._cover_thread.quit)
        self._cover_thread.finished.connect(self._cleanup_cover_worker)

        self.cover_generation_started.emit()
        self._cover_thread.start()

    def _on_cover_finished(self, relative_path: str):
        """封面生成成功"""
        self.cover_generation_finished.emit(relative_path)

    def _on_cover_failed(self, error_msg: str):
        """封面生成失败"""
        self.cover_generation_failed.emit(error_msg)

    def _cleanup_cover_worker(self):
        """清理 Worker 和线程"""
        if self._cover_worker:
            self._cover_worker.deleteLater()
            self._cover_worker = None
        if self._cover_thread:
            self._cover_thread.deleteLater()
            self._cover_thread = None

    @Slot(str, result=str)
    def resolve_cover_path(self, absolute_path: str) -> str:
        if not absolute_path or not self._workspace_root:
            return absolute_path
        try:
            return to_relative_path(absolute_path, self._workspace_root)
        except ValueError:
            return absolute_path

