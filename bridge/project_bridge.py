from __future__ import annotations

import json
import os
import re
import shutil
import uuid
from loguru import logger

from PySide6.QtCore import QObject, Property, Signal, Slot, QThread

from bridge.models.project_model import ProjectListModel
from bridge.workers import GeneralWorker
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
        self._image_service = None
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
        self._project_service.delete_project(project_id)
        project_dir = paths.projects_dir(paths.workspace_root())
        target = f"{project_dir}/{project_id}"
        if os.path.isdir(target):
            shutil.rmtree(target, ignore_errors=True)
        self.load_projects()
        self.project_deleted.emit(project_id)

    @Slot(int, result=str)
    def get_project_info(self, project_id: int) -> str:
        project = self._project_service.get_project(project_id)
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
        media_repo = self._session_manager.get_repo(MediaRepository)
        media_files = media_repo.list_with_filters(
            media_type=MediaType.VIDEO, conversation_ids=None,
        )
        pattern = re.compile(r"^\d+-\d+-\d+\.mp4$")
        return any(pattern.match(m.filename) for m in media_files)

    def set_image_service(self, image_service):
        self._image_service = image_service

    def set_workspace_root(self, workspace_root: str):
        self._workspace_root = workspace_root

    @Slot(int, str, str, str, str, str, str)
    def generate_cover_with_character(
        self, project_id: int, character_name: str, appearance: str,
        aspect_ratio: str, project_name: str, outline_content: str, design_image_path: str
    ) -> None:
        if not self._image_service:
            logger.error("ImageService 未设置")
            self.cover_generation_failed.emit("服务未初始化")
            return

        if not self._workspace_root:
            logger.error("workspace_root 未设置")
            self.cover_generation_failed.emit("工作目录未设置")
            return

        self.cover_generation_started.emit()

        def task():
            outline_summary = outline_content[:300] if outline_content else ""
            prompt = f"为视频项目《{project_name}》生成封面图。\n项目大纲：{outline_summary}\n主角：{character_name}，形象描述：{appearance}"
            size = self._get_image_size(aspect_ratio)

            project_dir = paths.project_dir(self._workspace_root, project_id)
            assets_dir = os.path.join(project_dir, ".assets")
            os.makedirs(assets_dir, exist_ok=True)

            cover_filename = f"cover_{uuid.uuid4().hex[:8]}.jpg"
            cover_path = os.path.join(assets_dir, cover_filename)

            local_path = self._image_service.generate(
                prompt=prompt,
                save_path=cover_path,
                size=size,
                negative_prompt="低质量，模糊，噪点，水印，文字",
                n=1,
            )

            workspace = paths.workspace_dir(self._workspace_root)
            relative_path = os.path.relpath(local_path, workspace)

            self._project_service.update_cover_image(project_id, relative_path)
            return relative_path

        def on_success(relative_path):
            logger.info(f"项目 {project_id} 封面图生成成功: {relative_path}")
            self.cover_generation_finished.emit(relative_path)
            self.load_projects()

        def on_error(error_msg):
            logger.error(f"项目 {project_id} 封面图生成失败: {error_msg}")
            self.cover_generation_failed.emit(error_msg)

        worker = GeneralWorker(task)
        worker.finished.connect(on_success)
        worker.failed.connect(on_error)

        thread = QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(thread.deleteLater)
        worker.finished.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)
        thread.start()

    @Slot(str, result=str)
    def resolve_cover_path(self, absolute_path: str) -> str:
        if not absolute_path or not self._workspace_root:
            return absolute_path
        workspace_dir = paths.workspace_dir(self._workspace_root)
        try:
            return os.path.relpath(absolute_path, workspace_dir).replace("\\", "/")
        except ValueError:
            return absolute_path

    def _get_image_size(self, aspect_ratio: str) -> str:
        size_map = {
            "1:1": "1280*1280",
            "3:4": "1104*1472",
            "4:3": "1472*1104",
            "9:16": "960*1696",
            "16:9": "1696*960",
        }
        return size_map.get(aspect_ratio, "1696*960")
