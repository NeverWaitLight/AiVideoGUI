from __future__ import annotations

import glob
import os
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, QThread, Signal

if TYPE_CHECKING:
    from di import ApplicationContainer

from utils import paths
from utils.image_processor import to_black_and_white
from utils.path_converter import to_relative_path


class CoverGenerationWorker(QObject):
    finished = Signal(str)
    failed = Signal(str)

    def __init__(
        self,
        project_id: int,
        project_name: str,
        aspect_ratio: str,
        outline_content: str,
        character_names: str,
        appearances: str,
        design_image_paths: str,
        visual_style: str,
        image_service,
        project_service,
        workspace_root: str,
        config_manager=None,
        session_manager=None,
        parent=None,
    ):
        super().__init__(parent)
        self._project_id = project_id
        self._project_name = project_name
        self._aspect_ratio = aspect_ratio
        self._outline_content = outline_content
        self._character_names = character_names
        self._appearances = appearances
        self._design_image_paths = design_image_paths
        self._visual_style = visual_style
        self._image_service = image_service
        self._project_service = project_service
        self._workspace_root = workspace_root
        self._config_manager = config_manager
        self._session_manager = session_manager

    def run(self):
        try:
            names_list = [n.strip() for n in self._character_names.split(",")]
            descriptions_list = [d.strip() for d in self._appearances.split("\n\n")]

            character_info_parts = []
            for i, (name, desc) in enumerate(zip(names_list, descriptions_list), start=1):
                character_info_parts.append(f"角色{i}：{name}\n形象描述：{desc}")
            character_info = "\n\n".join(character_info_parts)

            local_path = to_relative_path(
                os.path.join(
                    paths.projects_dir(self._workspace_root),
                    str(self._project_id),
                    f"cover-{self._project_id}.png",
                ),
                self._workspace_root,
            )

            provider_task_id, _chat_task_id = self._image_service.generate_cover_image(
                project_name=self._project_name,
                aspect_ratio=self._aspect_ratio,
                outline_content=self._outline_content,
                character_info=character_info,
                local_path=local_path,
                visual_style=self._visual_style,
                project_id=self._project_id,
            )

            from service.background.image_generation_worker import execute_image_generation
            image_path = execute_image_generation(
                provider_task_id=provider_task_id,
                config_manager=self._config_manager,
                session_manager=self._session_manager,
                workspace_root=self._workspace_root,
            )

            relative_path = to_relative_path(image_path, self._workspace_root)

            project = self._project_service.get_project(self._project_id)
            if project:
                self._project_service.update_project(
                    project_id=self._project_id,
                    name=project.name,
                    resolution=project.resolution,
                    aspect_ratio=project.aspect_ratio,
                    cover_image=relative_path,
                    visual_style_id=project.visual_style_id,
                )

            self.finished.emit(relative_path)

        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            self.failed.emit(error_msg)


class ScriptGenerateWorker(QThread):
    finished = Signal(str, list)
    failed = Signal(str)

    def __init__(self, text_service, outline_content: str,
                 project_id: int | None = None, project_name: str | None = None, parent=None):
        super().__init__(parent)
        self._text_service = text_service
        self._outline_content = outline_content
        self._project_id = project_id
        self._project_name = project_name

    def run(self):
        try:
            title, scenes, task_id = self._text_service.generate_script(
                self._outline_content,
                project_id=self._project_id,
                project_name=self._project_name,
            )
            self.finished.emit(title, scenes)
        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            self.failed.emit(error_msg)


class StoryboardGenerateWorker(QThread):
    finished = Signal(list)
    failed = Signal(str)

    def __init__(self, text_service, script_content: str, art_style: str = "",
                 project_id: int | None = None, project_name: str | None = None, parent=None):
        super().__init__(parent)
        self._text_service = text_service
        self._script_content = script_content
        self._art_style = art_style
        self._project_id = project_id
        self._project_name = project_name

    def run(self):
        try:
            result, task_id = self._text_service.generate_storyboard(
                self._script_content, self._art_style,
                project_id=self._project_id,
                project_name=self._project_name,
            )
            self.finished.emit(result)
        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            self.failed.emit(error_msg)


class CharacterWorker(QThread):
    finished = Signal(list)
    failed = Signal(str)

    def __init__(self, text_service, mode: str,
                 project_id: int | None = None, project_name: str | None = None, **kwargs):
        super().__init__()
        self._text_service = text_service
        self._mode = mode
        self._project_id = project_id
        self._project_name = project_name
        self._kwargs = kwargs

    def run(self):
        try:
            if self._mode == 'generate':
                characters, task_id = self._text_service.generate_characters(
                    outline_content=self._kwargs['outline_content'],
                    script_content=self._kwargs['script_content'],
                    user_requirement=self._kwargs['user_requirement'],
                    project_id=self._project_id,
                    project_name=self._project_name,
                )
            else:
                characters, task_id = self._text_service.optimize_characters(
                    outline_content=self._kwargs['outline_content'],
                    script_content=self._kwargs['script_content'],
                    current_characters=self._kwargs['current_characters'],
                    user_requirement=self._kwargs['user_requirement'],
                    project_id=self._project_id,
                    project_name=self._project_name,
                )
            self.finished.emit(characters)
        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            self.failed.emit(error_msg)


class OutlineOptimizeWorker(QThread):
    finished = Signal(str)
    failed = Signal(str)

    def __init__(
        self,
        text_service,
        original_content: str,
        user_requirement: str,
        project_id: int | None = None,
        project_name: str | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self._text_service = text_service
        self._original_content = original_content
        self._user_requirement = user_requirement
        self._project_id = project_id
        self._project_name = project_name

    def run(self):
        try:
            result, _task_id = self._text_service.optimize_story_outline(
                self._original_content,
                self._user_requirement,
                project_id=self._project_id,
                project_name=self._project_name,
            )
            self.finished.emit(result)
        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            self.failed.emit(error_msg)


class ScreenplayOptimizeWorker(QThread):
    finished = Signal(str, list)
    failed = Signal(str)

    def __init__(self, text_service, outline_content: str, current_script: str, user_requirement: str,
                 project_id: int | None = None, project_name: str | None = None, parent=None):
        super().__init__(parent)
        self._text_service = text_service
        self._outline_content = outline_content
        self._current_script = current_script
        self._user_requirement = user_requirement
        self._project_id = project_id
        self._project_name = project_name

    def run(self):
        try:
            title, scenes, task_id = self._text_service.optimize_screenplay(
                self._outline_content,
                self._current_script,
                self._user_requirement,
                project_id=self._project_id,
                project_name=self._project_name,
            )
            self.finished.emit(title, scenes)
        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            self.failed.emit(error_msg)


class StoryboardOptimizeWorker(QThread):
    finished = Signal(list)
    failed = Signal(str)

    def __init__(self, text_service, outline_content: str, script_content: str,
                 character_content: str, current_storyboard: str, user_requirement: str,
                 project_id: int | None = None, project_name: str | None = None, parent=None):
        super().__init__(parent)
        self._text_service = text_service
        self._outline_content = outline_content
        self._script_content = script_content
        self._character_content = character_content
        self._current_storyboard = current_storyboard
        self._user_requirement = user_requirement
        self._project_id = project_id
        self._project_name = project_name

    def run(self):
        try:
            shots, task_id = self._text_service.optimize_storyboard(
                self._outline_content,
                self._script_content,
                self._character_content,
                self._current_storyboard,
                self._user_requirement,
                project_id=self._project_id,
                project_name=self._project_name,
            )
            self.finished.emit(shots)
        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            self.failed.emit(error_msg)


class DesignImageWorker(QThread):
    finished = Signal(str)
    failed = Signal(str)
    progress_update = Signal(str)

    def __init__(
        self, image_service, storyboard_service,
        storyboard, shot_size_text: str, character_info: str, project_id: int,
        visual_style: str = "", project_name: str | None = None,
        config_manager=None, session_manager=None, workspace_root: str | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self._image_service = image_service
        self._storyboard_service = storyboard_service
        self._storyboard = storyboard
        self._shot_size_text = shot_size_text
        self._character_info = character_info
        self._project_id = project_id
        self._visual_style = visual_style
        self._project_name = project_name
        self._config_manager = config_manager
        self._session_manager = session_manager
        self._workspace_root = workspace_root

    def run(self):
        try:
            self.progress_update.emit("正在生成设计图提示词...")
            local_path = to_relative_path(
                os.path.join(
                    paths.projects_dir(paths.workspace_root()),
                    str(self._project_id),
                    f"design-{self._storyboard.scene_number}-{self._storyboard.shot_number}.png",
                ),
                paths.workspace_root(),
            )

            provider_task_id, _chat_task_id = self._image_service.generate_design_image(
                content=self._storyboard.content,
                local_path=local_path,
                shot_size=self._shot_size_text,
                camera_movement=self._storyboard.camera_movement,
                notes=self._storyboard.notes,
                character_info=self._character_info,
                visual_style=self._visual_style,
                project_id=self._project_id,
                project_name=self._project_name,
                caller_id=str(self._storyboard.id),
            )

            self.progress_update.emit("图片生成中，请稍候...")

            from service.background.image_generation_worker import execute_image_generation
            image_path = execute_image_generation(
                provider_task_id=provider_task_id,
                config_manager=self._config_manager,
                session_manager=self._session_manager,
                workspace_root=self._workspace_root,
            )

            to_black_and_white(image_path)

            self._storyboard_service.update_storyboard(
                storyboard_id=self._storyboard.id, design_image=image_path,
            )
            self.finished.emit(to_relative_path(image_path, self._workspace_root))

        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            self.failed.emit(error_msg)


class BatchDesignImageWorker(QThread):
    progress_update = Signal(int, str, str)
    shot_design_started = Signal(int)
    shot_design_done = Signal(int, str)
    shot_design_failed = Signal(int)
    finished = Signal(int, int)
    failed = Signal(str)

    def __init__(
        self, image_service, storyboard_service, character_service,
        shot_list: list[dict], visual_style: str = "", project_name: str | None = None,
        config_manager=None, session_manager=None, workspace_root: str | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self._image_service = image_service
        self._storyboard_service = storyboard_service
        self._character_service = character_service
        self._shot_list = shot_list
        self._visual_style = visual_style
        self._project_name = project_name
        self._config_manager = config_manager
        self._session_manager = session_manager
        self._workspace_root = workspace_root

    def run(self):
        success_count = 0
        total = len(self._shot_list)

        shot_size_map = {
            "extreme_close_up": "特写", "close_up": "近景", "medium_shot": "中景",
            "full_shot": "全景", "long_shot": "远景", "extreme_long_shot": "大远景",
        }

        for idx, shot_data in enumerate(self._shot_list, start=1):
            storyboard_id = shot_data["storyboard_id"]
            self.shot_design_started.emit(storyboard_id)
            try:
                project_id = shot_data["project_id"]
                scene_number = shot_data["scene_number"]
                shot_number = shot_data["shot_number"]

                self.progress_update.emit(
                    idx - 1,
                    f"正在生成 {scene_number}-{shot_number} 镜设计图...",
                    f"({idx}/{total})",
                )

                content = shot_data["content"]
                characters = self._character_service.list_characters(project_id)
                matched_chars = [
                    c for c in characters
                    if c.name in content or c.ref_code in content
                ]

                character_info = ""
                if matched_chars:
                    parts = []
                    for c in matched_chars:
                        traits = self._character_service.extract_fixed_traits(c.description)
                        if traits:
                            parts.append(f"{c.name}（{c.ref_code}）：{traits}")
                    character_info = "\n".join(parts)

                shot_size_text = shot_size_map.get(shot_data["shot_size"].value, "中景")
                local_path = to_relative_path(
                    os.path.join(
                        paths.projects_dir(paths.workspace_root()),
                        str(project_id),
                        f"design-{scene_number}-{shot_number}.png",
                    ),
                    paths.workspace_root(),
                )

                provider_task_id, _chat_task_id = self._image_service.generate_design_image(
                    content=content,
                    local_path=local_path,
                    shot_size=shot_size_text,
                    camera_movement=shot_data.get("camera_movement", ""),
                    notes=shot_data.get("notes", ""),
                    character_info=character_info,
                    visual_style=self._visual_style,
                    project_id=project_id,
                    project_name=self._project_name,
                    caller_id=str(storyboard_id),
                )

                from service.background.image_generation_worker import execute_image_generation
                image_path = execute_image_generation(
                    provider_task_id=provider_task_id,
                    config_manager=self._config_manager,
                    session_manager=self._session_manager,
                    workspace_root=self._workspace_root,
                )

                to_black_and_white(image_path)

                self._storyboard_service.update_storyboard(
                    storyboard_id=storyboard_id, design_image=image_path,
                )
                relative_path = to_relative_path(image_path, self._workspace_root)

                success_count += 1
                self.shot_design_done.emit(storyboard_id, relative_path)
                self.progress_update.emit(idx, f"完成 {scene_number}-{shot_number}", f"({idx}/{total})")

            except Exception:
                self.shot_design_failed.emit(storyboard_id)
                self.progress_update.emit(idx, f"生成失败", f"({idx}/{total})")

        self.finished.emit(success_count, total)


class CharacterDesignImageWorker(QThread):
    finished = Signal(str)
    failed = Signal(str)
    progress_update = Signal(str)

    def __init__(self, image_service, character_service, character, project_id: int,
                 user_requirement: str = "", visual_style: str = "", project_name: str | None = None,
                 config_manager=None, session_manager=None, workspace_root: str | None = None,
                 parent=None):
        super().__init__(parent)
        self._image_service = image_service
        self._character_service = character_service
        self._character = character
        self._project_id = project_id
        self._project_name = project_name
        self._user_requirement = user_requirement
        self._visual_style = visual_style
        self._config_manager = config_manager
        self._session_manager = session_manager
        self._workspace_root = workspace_root

    def run(self):
        try:
            self.progress_update.emit("正在生成角色设计图提示词...")
            local_path = to_relative_path(
                os.path.join(
                    paths.projects_dir(paths.workspace_root()),
                    str(self._project_id),
                    f"char-{self._character.uuid}.png",
                ),
                paths.workspace_root(),
            )

            provider_task_id, _chat_task_id = self._image_service.generate_character_design_image(
                character_name=self._character.name,
                description=self._character.description,
                local_path=local_path,
                user_requirement=self._user_requirement,
                visual_style=self._visual_style,
                project_id=self._project_id,
                project_name=self._project_name,
                caller_id=self._character.uuid,
            )

            self.progress_update.emit("图片生成中，请稍候...")

            from service.background.image_generation_worker import execute_image_generation
            image_path = execute_image_generation(
                provider_task_id=provider_task_id,
                config_manager=self._config_manager,
                session_manager=self._session_manager,
                workspace_root=self._workspace_root,
            )

            from loguru import logger
            logger.info(f"角色设计图生成完成，开始更新数据库：char_uuid={self._character.uuid}, image_path={image_path}")

            self._character_service.update_character(
                character_uuid=self._character.uuid, design_image=image_path,
            )
            logger.info(f"角色设计图已保存到数据库：{image_path}")

            relative_path = to_relative_path(image_path, self._workspace_root)
            self.finished.emit(relative_path)

        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            self.failed.emit(error_msg)


class CharacterRefineWorker(QThread):
    finished = Signal(str)
    failed = Signal(str)

    def __init__(self, text_service, character_name: str, current_description: str,
                 user_requirement: str, project_id: int | None = None,
                 project_name: str | None = None, parent=None):
        super().__init__(parent)
        self._text_service = text_service
        self._character_name = character_name
        self._current_description = current_description
        self._user_requirement = user_requirement
        self._project_id = project_id
        self._project_name = project_name

    def run(self):
        try:
            result, task_id = self._text_service.refine_character_description(
                character_name=self._character_name,
                current_description=self._current_description,
                user_requirement=self._user_requirement,
                project_id=self._project_id,
                project_name=self._project_name,
            )
            self.finished.emit(result)
        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            self.failed.emit(error_msg)


class OptimizeWorker(QThread):
    finished = Signal(str)
    failed = Signal(str)

    def __init__(self, text_service, messages: list[dict],
                 project_id: int | None = None, project_name: str | None = None,
                 module: str = "outline", context: str | None = None, parent=None):
        super().__init__(parent)
        self._text_service = text_service
        self._messages = messages
        self._project_id = project_id
        self._project_name = project_name
        self._module = module
        self._context = context

    def run(self):
        try:
            reply, task_id = self._text_service.chat(
                self._messages,
                project_id=self._project_id,
                project_name=self._project_name,
                module=self._module,
                context=self._context,
            )
            self.finished.emit(reply)
        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            self.failed.emit(error_msg)


class GeneralWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, task_func, parent=None):
        super().__init__(parent)
        self._task_func = task_func

    def run(self):
        try:
            result = self._task_func()
            self.finished.emit(result)
        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            self.failed.emit(error_msg)


class VideoExportWorker(QThread):
    finished = Signal(str)
    failed = Signal(str)
    progress = Signal(int, str)

    def __init__(self, media_service, project_id: int, output_path: str, parent=None):
        super().__init__(parent)
        self._media_service = media_service
        self._project_id = project_id
        self._output_path = output_path

    def run(self):
        try:
            output_path = self._media_service.export_project_video(
                project_id=self._project_id,
                output_path=self._output_path,
                progress_callback=lambda percent, msg: self.progress.emit(percent, msg)
            )
            self.finished.emit(output_path)
        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            self.failed.emit(error_msg)


class BatchGenerationController(QThread):
    progress = Signal(int, int, str)
    all_done = Signal(int, int)
    terminated = Signal(int, int)
    take_created = Signal()

    def __init__(
        self, shot_list: list[dict], video_service, signal_emitter: QObject,
        provider_name: str, project, provider_cfg,
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self._shot_list = shot_list
        self._service = video_service
        self._signal_emitter = signal_emitter
        self._provider_name = provider_name
        self._project = project
        self._provider_cfg = provider_cfg
        self._success = 0
        self._failed = 0
        self._submitted_task_ids: set[str] = set()
        self._stopped = False

    def run(self) -> None:
        self._stopped = False
        self._signal_emitter.task_finished.connect(self._on_task_finished)
        self._signal_emitter.task_failed.connect(self._on_task_failed)

        submitted = 0
        for i, shot in enumerate(self._shot_list):
            if self._stopped:
                break

            scene_number = shot["scene_number"]
            shot_number = shot["shot_number"]
            reference_images = shot.get("reference_images", [])

            self.progress.emit(submitted, len(self._shot_list), f"正在提交场{scene_number}镜{shot_number}...")

            try:
                params = (self._provider_cfg.default_params if self._provider_cfg else {}).copy()
                params["resolution"] = self._project.resolution
                params["ratio"] = self._project.aspect_ratio

                duration = shot.get("duration")
                if duration is not None:
                    params["duration"] = int(duration)

                provider_task_id = self._service.submit_shot_video(
                    storyboard=shot["storyboard"],
                    scene=shot.get("scene"),
                    prev_shot=shot.get("prev_shot"),
                    next_shot=shot.get("next_shot"),
                    reference_images=reference_images,
                    reference_images_info=shot.get("reference_images_info"),
                    visual_style=shot.get("visual_style"),
                    provider_name=self._provider_name,
                    params=params,
                    project_id=self._project.id,
                    project_name=self._project.name,
                )
                self._submitted_task_ids.add(provider_task_id)
                submitted += 1
                self.take_created.emit()

            except Exception:
                self._failed += 1
                self.progress.emit(submitted, len(self._shot_list), f"场{scene_number}镜{shot_number} 提交失败")

        if submitted > 0:
            self.progress.emit(submitted, len(self._shot_list), f"已提交 {submitted} 个任务，等待生成完成...")
        else:
            self._cleanup_and_finish()

    def stop(self) -> None:
        if self._stopped:
            return
        self._stopped = True
        self.progress.emit(0, len(self._shot_list), "正在停止...")
        self._cleanup_and_terminate()

    def _cleanup_and_terminate(self) -> None:
        try:
            self._signal_emitter.task_finished.disconnect(self._on_task_finished)
            self._signal_emitter.task_failed.disconnect(self._on_task_failed)
        except RuntimeError:
            pass
        self.terminated.emit(self._success, self._failed)

    def _cleanup_and_finish(self) -> None:
        try:
            self._signal_emitter.task_finished.disconnect(self._on_task_finished)
            self._signal_emitter.task_failed.disconnect(self._on_task_failed)
        except RuntimeError:
            pass
        self.all_done.emit(self._success, self._failed)

    def _on_task_finished(self, provider_task_id: str, save_path: str, storyboard_id: int = 0) -> None:
        if provider_task_id not in self._submitted_task_ids:
            return

        self._success += 1
        completed = self._success + self._failed
        total_submitted = len(self._submitted_task_ids)
        self.progress.emit(completed, total_submitted, f"已完成 {self._success}/{total_submitted}，失败 {self._failed}")

        if completed >= total_submitted:
            self._cleanup_and_finish()

    def _on_task_failed(self, provider_task_id: str, error: str) -> None:
        if provider_task_id not in self._submitted_task_ids:
            return

        self._failed += 1
        completed = self._success + self._failed
        total_submitted = len(self._submitted_task_ids)
        self.progress.emit(completed, total_submitted, f"已完成 {self._success}/{total_submitted}，失败 {self._failed}")

        if completed >= total_submitted:
            self._cleanup_and_finish()
