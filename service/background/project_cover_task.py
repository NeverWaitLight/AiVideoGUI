from __future__ import annotations

import os
import uuid
from loguru import logger
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Signal

from service.background.task_base import BackgroundTask, TaskType
from storage.session_manager import SessionManager
from storage.repositories.project_repository import ProjectRepository
from storage.repositories.story_outline_repository import StoryOutlineRepository

if TYPE_CHECKING:
    from service.image_service import ImageService


class ProjectCoverGenerationTask(BackgroundTask):

    def __init__(
        self,
        session_manager: SessionManager,
        image_service: ImageService,
        workspace_root: str,
    ) -> None:
        super().__init__(TaskType.ONE_TIME, "project_cover_generation")
        self._sm = session_manager
        self._image_service = image_service
        self._workspace_root = workspace_root
        self._completed = False

        self._signal_emitter = _SignalEmitter()

    @property
    def signal_emitter(self) -> QObject:
        return self._signal_emitter

    def execute(self) -> None:
        logger.info("开始扫描项目并生成封面图")

        project_repo = self._sm.get_repo(ProjectRepository)
        outline_repo = self._sm.get_repo(StoryOutlineRepository)

        projects = project_repo.list_all()
        logger.info(f"共找到 {len(projects)} 个项目")

        generated_count = 0
        failed_count = 0

        for project in projects:
            if project.cover_image:
                logger.debug(f"项目 {project.name}（ID: {project.id}）已有封面，跳过")
                continue

            outline = outline_repo.get_by_project(project.id)
            if not outline or not outline.content.strip():
                logger.debug(f"项目 {project.name}（ID: {project.id}）没有大纲，跳过")
                continue

            try:
                self._signal_emitter.cover_generation_started.emit(project.id)

                self._generate_cover_for_project(project.id, project.name, project.aspect_ratio, outline.content)
                generated_count += 1
                logger.info(f"为项目 {project.name}（ID: {project.id}）生成封面成功")

                self._signal_emitter.cover_generation_finished.emit(project.id)
            except Exception as e:
                failed_count += 1
                logger.error(f"为项目 {project.name}（ID: {project.id}）生成封面失败：{e}")

                self._signal_emitter.cover_generation_failed.emit(project.id, str(e))

        self._completed = True
        logger.info(f"封面生成任务完成，成功：{generated_count}，失败：{failed_count}")

    def _generate_cover_for_project(
        self,
        project_id: int,
        project_name: str,
        aspect_ratio: str,
        outline_content: str,
    ) -> None:
        outline_summary = outline_content[:500]
        prompt = f"为视频项目《{project_name}》生成封面图。项目大纲：{outline_summary}"

        size = self._get_image_size(aspect_ratio)

        from utils import paths
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

        from utils import paths
        workspace = paths.workspace_dir(self._workspace_root)
        relative_path = os.path.relpath(local_path, workspace)

        project_repo = self._sm.get_repo(ProjectRepository)
        self._sm.begin_write()
        try:
            project_repo.update_cover_image(project_id, relative_path)
            self._sm.commit_write()
        except Exception:
            self._sm.rollback_write()
            raise

    def _get_image_size(self, aspect_ratio: str) -> str:
        size_map = {
            "1:1": "1280*1280",
            "3:4": "1104*1472",
            "4:3": "1472*1104",
            "9:16": "960*1696",
            "16:9": "1696*960",
        }
        return size_map.get(aspect_ratio, "1696*960")

    def should_continue(self) -> bool:
        return not self._completed


class _SignalEmitter(QObject):

    cover_generation_started = Signal(int)
    cover_generation_finished = Signal(int)
    cover_generation_failed = Signal(int, str)
