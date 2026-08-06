from __future__ import annotations

import glob
import os
import re
from loguru import logger
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, QThread, Signal

if TYPE_CHECKING:
    from di import ApplicationContainer

from utils import paths
from utils.image_processor import to_black_and_white


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
            title, scenes = self._text_service.generate_script(
                self._outline_content,
                project_id=self._project_id,
                project_name=self._project_name,
            )
            self.finished.emit(title, scenes)
        except Exception as e:
            logger.exception("生成剧本失败")
            self.failed.emit(str(e))


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
            result = self._text_service.generate_storyboard(
                self._script_content, self._art_style,
                project_id=self._project_id,
                project_name=self._project_name,
            )
            self.finished.emit(result)
        except Exception as e:
            logger.exception("生成分镜失败")
            self.failed.emit(str(e))


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
                characters = self._text_service.generate_characters(
                    outline_content=self._kwargs['outline_content'],
                    script_content=self._kwargs['script_content'],
                    user_requirement=self._kwargs['user_requirement'],
                    project_id=self._project_id,
                    project_name=self._project_name,
                )
            else:
                characters = self._text_service.optimize_characters(
                    outline_content=self._kwargs['outline_content'],
                    script_content=self._kwargs['script_content'],
                    current_characters=self._kwargs['current_characters'],
                    user_requirement=self._kwargs['user_requirement'],
                    project_id=self._project_id,
                    project_name=self._project_name,
                )
            self.finished.emit(characters)
        except Exception as e:
            logger.exception(f"{'生成' if self._mode == 'generate' else '优化'}角色失败")
            self.failed.emit(str(e))


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
            title, scenes = self._text_service.optimize_screenplay(
                self._outline_content,
                self._current_script,
                self._user_requirement,
                project_id=self._project_id,
                project_name=self._project_name,
            )
            self.finished.emit(title, scenes)
        except Exception as e:
            logger.exception("优化剧本失败")
            self.failed.emit(str(e))


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
            shots = self._text_service.optimize_storyboard(
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
            logger.exception("优化分镜失败")
            self.failed.emit(str(e))


class DesignImageWorker(QThread):
    finished = Signal(str)
    failed = Signal(str)
    progress_update = Signal(str)

    def __init__(
        self, text_service, image_service, storyboard_service,
        storyboard, shot_size_text: str, character_info: str, project_id: int,
        visual_style: str = "", project_name: str | None = None, parent=None,
    ):
        super().__init__(parent)
        self._text_service = text_service
        self._image_service = image_service
        self._storyboard_service = storyboard_service
        self._storyboard = storyboard
        self._shot_size_text = shot_size_text
        self._character_info = character_info
        self._project_id = project_id
        self._visual_style = visual_style
        self._project_name = project_name

    def run(self):
        try:
            self.progress_update.emit("正在生成设计图提示词...")
            image_prompt = self._text_service.generate_design_image_prompt(
                visual_content=self._storyboard.visual_content,
                shot_size=self._shot_size_text,
                camera_movement=self._storyboard.camera_movement,
                dialogue=self._storyboard.dialogue,
                notes=self._storyboard.notes,
                character_info=self._character_info,
                visual_style=self._visual_style,
                project_id=self._project_id,
                project_name=self._project_name,
            )
            logger.info(f"设计图提示词：{image_prompt}")

            self.progress_update.emit("正在调用图片生成模型...")
            save_path = os.path.join(
                paths.projects_dir(paths.workspace_root()),
                str(self._project_id),
                f"design-{self._storyboard.scene_number}-{self._storyboard.shot_number}.png",
            )
            result_path = self._image_service.generate(
                prompt=image_prompt, save_path=save_path,
                project_id=self._project_id,
                project_name=self._project_name,
                module="storyboard",
                context="分镜设计图生成",
            )
            to_black_and_white(result_path)

            self._storyboard_service.update_storyboard(
                storyboard_id=self._storyboard.id, design_image=result_path,
            )
            logger.info(f"设计图生成完成：{result_path}")
            self.finished.emit(result_path)
        except Exception as e:
            logger.exception("生成设计图失败")
            self.failed.emit(str(e))


class BatchDesignImageWorker(QThread):
    progress_update = Signal(int, str, str)
    shot_design_done = Signal(int, str)
    finished = Signal(int, int)
    failed = Signal(str)

    def __init__(
        self, text_service, image_service, storyboard_service, character_service,
        shot_list: list[dict], visual_style: str = "", project_name: str | None = None, parent=None,
    ):
        super().__init__(parent)
        self._text_service = text_service
        self._image_service = image_service
        self._storyboard_service = storyboard_service
        self._character_service = character_service
        self._shot_list = shot_list
        self._visual_style = visual_style
        self._project_name = project_name

    def run(self):
        success_count = 0
        total = len(self._shot_list)

        shot_size_map = {
            "extreme_close_up": "特写", "close_up": "近景", "medium_shot": "中景",
            "full_shot": "全景", "long_shot": "远景", "extreme_long_shot": "大远景",
        }

        for idx, shot_data in enumerate(self._shot_list, start=1):
            try:
                storyboard_id = shot_data["storyboard_id"]
                project_id = shot_data["project_id"]
                scene_number = shot_data["scene_number"]
                shot_number = shot_data["shot_number"]

                self.progress_update.emit(
                    idx - 1,
                    f"正在生成 {scene_number}-{shot_number} 镜设计图...",
                    f"({idx}/{total})",
                )

                visual_content = shot_data["visual_content"]
                characters = self._character_service.list_characters(project_id)
                matched_chars = [
                    c for c in characters
                    if c.name in visual_content or c.ref_code in visual_content
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
                image_prompt = self._text_service.generate_design_image_prompt(
                    visual_content=visual_content,
                    shot_size=shot_size_text,
                    camera_movement=shot_data.get("camera_movement", ""),
                    dialogue=shot_data.get("dialogue", ""),
                    notes=shot_data.get("notes", ""),
                    character_info=character_info,
                    visual_style=self._visual_style,
                    project_id=project_id,
                    project_name=self._project_name,
                )

                save_path = os.path.join(
                    paths.projects_dir(paths.workspace_root()),
                    str(project_id),
                    f"design-{scene_number}-{shot_number}.png",
                )
                result_path = self._image_service.generate(
                    prompt=image_prompt, save_path=save_path,
                    project_id=project_id,
                    project_name=self._project_name,
                    module="storyboard",
                    context="分镜设计图批量生成",
                )
                to_black_and_white(result_path)

                self._storyboard_service.update_storyboard(
                    storyboard_id=storyboard_id, design_image=result_path,
                )
                success_count += 1
                self.shot_design_done.emit(storyboard_id, result_path)
                self.progress_update.emit(idx, f"完成 {scene_number}-{shot_number}", f"({idx}/{total})")

            except Exception as e:
                logger.warning(f"批量设计图生成 [{idx}/{total}] 失败：{e}")
                self.progress_update.emit(idx, f"失败：{e}", f"({idx}/{total})")

        self.finished.emit(success_count, total)


class CharacterDesignImageWorker(QThread):
    finished = Signal(str)
    failed = Signal(str)
    progress_update = Signal(str)

    def __init__(self, text_service, image_service, character_service, character, project_id: int,
                 user_requirement: str = "", visual_style: str = "", project_name: str | None = None, parent=None):
        super().__init__(parent)
        self._text_service = text_service
        self._image_service = image_service
        self._character_service = character_service
        self._character = character
        self._project_id = project_id
        self._project_name = project_name
        self._user_requirement = user_requirement
        self._visual_style = visual_style

    def run(self):
        try:
            self.progress_update.emit("正在生成角色设计图提示词...")
            image_prompt = self._text_service.generate_character_design_image_prompt(
                character_name=self._character.name,
                description=self._character.description,
                user_requirement=self._user_requirement,
                visual_style=self._visual_style,
                project_id=self._project_id,
                project_name=self._project_name,
            )
            logger.info(f"角色设计图提示词：{image_prompt}")

            self.progress_update.emit("正在调用图片生成模型...")
            save_path = os.path.join(
                paths.projects_dir(paths.workspace_root()),
                str(self._project_id),
                f"char-{self._character.uuid}.png",
            )
            result_path = self._image_service.generate(
                prompt=image_prompt, save_path=save_path,
                project_id=self._project_id,
                project_name=self._project_name,
                module="character",
                context=f"角色设计图生成 - {self._character.name}",
            )

            self._character_service.update_character(
                character_uuid=self._character.uuid, design_image=result_path,
            )
            logger.info(f"角色设计图生成完成：{result_path}")
            self.finished.emit(result_path)
        except Exception as e:
            logger.exception("生成角色设计图失败")
            self.failed.emit(str(e))


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
            result = self._text_service.refine_character_description(
                character_name=self._character_name,
                current_description=self._current_description,
                user_requirement=self._user_requirement,
                project_id=self._project_id,
                project_name=self._project_name,
            )
            self.finished.emit(result)
        except Exception as e:
            logger.exception("修改角色描述失败")
            self.failed.emit(str(e))


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
            reply = self._text_service.chat(
                self._messages,
                project_id=self._project_id,
                project_name=self._project_name,
                module=self._module,
                context=self._context,
            )
            self.finished.emit(reply)
        except Exception as e:
            logger.exception("AI 优化失败")
            self.failed.emit(str(e))


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
            logger.exception("任务执行失败")
            self.failed.emit(str(e))


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
            logger.exception("视频导出失败")
            self.failed.emit(str(e))
        except Exception as e:
            logger.exception("任务执行失败")
            self.failed.emit(str(e))


class BatchGenerationController(QThread):
    progress = Signal(int, int, str)
    all_done = Signal(int, int)
    terminated = Signal(int, int)

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

        gen_counts = self._scan_existing_gen_counts()

        submitted = 0
        for i, shot in enumerate(self._shot_list):
            if self._stopped:
                break

            scene_number = shot["scene_number"]
            shot_number = shot["shot_number"]
            prompt = shot["prompt"]
            project_id = shot["project_id"]
            shot_id = shot.get("shot_id", 0)
            reference_images = shot.get("reference_images", [])

            self.progress.emit(submitted, len(self._shot_list), f"正在提交场{scene_number}镜{shot_number}...")

            try:
                params = (self._provider_cfg.default_params if self._provider_cfg else {}).copy()
                params["resolution"] = self._project.resolution
                params["ratio"] = self._project.aspect_ratio

                duration = shot.get("duration")
                if duration is not None:
                    params["duration"] = int(duration)

                key = (scene_number, shot_number)
                gen_counts[key] = gen_counts.get(key, 0) + 1
                save_path = os.path.join(
                    paths.projects_dir(paths.workspace_root()),
                    str(project_id), f"{scene_number}-{shot_number}-{gen_counts[key]}.mp4",
                )

                provider_task_id = self._service.submit_task(
                    prompt=prompt,
                    provider_name=self._provider_name,
                    params=params,
                    save_path=save_path,
                    storyboard_id=shot_id,
                    reference_images=reference_images,
                    project_id=self._project.id,
                    project_name=self._project.name,
                )
                self._submitted_task_ids.add(provider_task_id)
                submitted += 1
                mode_info = f"(r2v, {len(reference_images)}张)" if reference_images else "(t2v)"
                logger.info(f"批量生成 [{submitted}/{len(self._shot_list)}] 场{scene_number}镜{shot_number} 已提交 {mode_info}")

            except Exception as e:
                logger.exception(f"批量生成提交失败：场{scene_number}镜{shot_number}")
                self._failed += 1
                self.progress.emit(submitted, len(self._shot_list), f"场{scene_number}镜{shot_number} 提交失败：{e}")

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

    def _scan_existing_gen_counts(self) -> dict[tuple[int, int], int]:
        """扫描项目目录中已有的视频文件，返回每个 (场次, 镜头) 的最大生成次数。"""
        counts: dict[tuple[int, int], int] = {}
        project_dir = os.path.join(
            paths.projects_dir(paths.workspace_root()),
            str(self._project.id),
        )
        if not os.path.isdir(project_dir):
            return counts
        pattern = re.compile(r"^(\d+)-(\d+)-(\d+)\.mp4$")
        for filename in os.listdir(project_dir):
            m = pattern.match(filename)
            if m:
                key = (int(m.group(1)), int(m.group(2)))
                gen = int(m.group(3))
                counts[key] = max(counts.get(key, 0), gen)
        return counts

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
