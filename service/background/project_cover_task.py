"""项目封面自动生成任务：扫描项目并为有大纲但无封面的项目生成封面图。"""

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
    """项目封面自动生成任务（一次性任务，被业务逻辑触发）。

    工作流程：
    1. 扫描所有项目
    2. 筛选出没有封面但有大纲的项目
    3. 使用大纲内容调用文生图 API 生成封面
    4. 下载封面到项目隐藏文件夹（.assets/cover.jpg）
    5. 更新项目的 cover_image 字段

    使用组合模式持有信号发射器，用于通知 UI 生成进度。
    """

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

        # 创建信号发射器（组合模式）
        self._signal_emitter = _SignalEmitter()

    @property
    def signal_emitter(self) -> QObject:
        """返回信号发射器（供外部连接信号）。"""
        return self._signal_emitter

    def execute(self) -> None:
        """执行封面生成任务。"""
        logger.info("开始扫描项目并生成封面图")

        project_repo = self._sm.get_repo(ProjectRepository)
        outline_repo = self._sm.get_repo(StoryOutlineRepository)

        # 查询所有项目
        projects = project_repo.list_all()
        logger.info(f"共找到 {len(projects)} 个项目")

        generated_count = 0
        failed_count = 0

        for project in projects:
            # 跳过已有封面的项目
            if project.cover_image:
                logger.debug(f"项目 {project.name}（ID: {project.id}）已有封面，跳过")
                continue

            # 检查项目是否有大纲
            outline = outline_repo.get_by_project(project.id)
            if not outline or not outline.content.strip():
                logger.debug(f"项目 {project.name}（ID: {project.id}）没有大纲，跳过")
                continue

            # 生成封面
            try:
                # 发送开始信号
                self._signal_emitter.cover_generation_started.emit(project.id)

                self._generate_cover_for_project(project.id, project.name, project.aspect_ratio, outline.content)
                generated_count += 1
                logger.info(f"为项目 {project.name}（ID: {project.id}）生成封面成功")

                # 发送完成信号
                self._signal_emitter.cover_generation_finished.emit(project.id)
            except Exception as e:
                failed_count += 1
                logger.error(f"为项目 {project.name}（ID: {project.id}）生成封面失败：{e}")

                # 发送失败信号
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
        """为单个项目生成封面图。

        Args:
            project_id: 项目 ID
            project_name: 项目名称
            aspect_ratio: 宽高比（如 "16:9"）
            outline_content: 大纲内容
        """
        # 构建 Prompt（使用大纲前 500 字符）
        outline_summary = outline_content[:500]
        prompt = f"为视频项目《{project_name}》生成封面图。项目大纲：{outline_summary}"

        # 映射宽高比到图片尺寸
        size = self._get_image_size(aspect_ratio)

        # 创建项目隐藏资源目录
        from utils import paths
        project_dir = paths.project_dir(self._workspace_root, project_id)
        assets_dir = os.path.join(project_dir, ".assets")
        os.makedirs(assets_dir, exist_ok=True)

        # 生成唯一文件名
        cover_filename = f"cover_{uuid.uuid4().hex[:8]}.jpg"
        cover_path = os.path.join(assets_dir, cover_filename)

        # 调用文生图服务
        local_path = self._image_service.generate(
            prompt=prompt,
            save_path=cover_path,
            size=size,
            negative_prompt="低质量，模糊，噪点，水印，文字",
            n=1,
        )

        # 更新项目封面路径（相对于 workspace 的路径）
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
        """根据宽高比映射到文生图 API 支持的尺寸。

        Args:
            aspect_ratio: 宽高比字符串（如 "16:9"）

        Returns:
            图片尺寸字符串（如 "1696*960"）
        """
        size_map = {
            "1:1": "1280*1280",
            "3:4": "1104*1472",
            "4:3": "1472*1104",
            "9:16": "960*1696",
            "16:9": "1696*960",
        }
        return size_map.get(aspect_ratio, "1696*960")  # 默认 16:9

    def should_continue(self) -> bool:
        """判断任务是否应该继续执行。

        Returns:
            False 表示任务已完成（一次性任务执行一次后返回 False）
        """
        return not self._completed


class _SignalEmitter(QObject):
    """信号发射器（独立的 QObject，避免多继承元类冲突）。"""

    cover_generation_started = Signal(int)  # project_id
    cover_generation_finished = Signal(int)  # project_id
    cover_generation_failed = Signal(int, str)  # project_id, error_message

