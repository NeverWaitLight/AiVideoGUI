from __future__ import annotations

import glob
import os
import threading
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, QThread, Signal

if TYPE_CHECKING:
    from di import ApplicationContainer

from utils.prompt_sanitize import flatten_prompt_text


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
        prompt_extend: bool = True,
        negative_prompt: str = "",
        use_prev_shot_last_frame: bool = True,
        cross_scene_prev_frame: bool = False,
        prev_shot_frame_service=None,
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self._shot_list = shot_list
        self._service = video_service
        self._signal_emitter = signal_emitter
        self._provider_name = provider_name
        self._project = project
        self._provider_cfg = provider_cfg
        self._prompt_extend = prompt_extend
        self._negative_prompt = negative_prompt
        self._use_prev_shot_last_frame = use_prev_shot_last_frame
        self._cross_scene_prev_frame = cross_scene_prev_frame
        self._prev_frame_service = prev_shot_frame_service
        self._success = 0
        self._failed = 0
        self._submitted_task_ids: set[str] = set()
        self._stopped = False

    def run(self) -> None:
        self._stopped = False
        if self._use_prev_shot_last_frame:
            self._run_serial_with_prev_frame()
        else:
            self._run_parallel()

    def _build_params(self, shot: dict) -> dict:
        params = (self._provider_cfg.default_params if self._provider_cfg else {}).copy()
        params["resolution"] = self._project.resolution
        params["ratio"] = self._project.aspect_ratio

        duration = shot.get("duration")
        if duration is not None:
            params["duration"] = int(duration)

        params["prompt_extend"] = self._prompt_extend

        cleaned_negative_prompt = flatten_prompt_text(self._negative_prompt)
        if cleaned_negative_prompt:
            params["negative_prompt"] = cleaned_negative_prompt
        return params

    def _resolve_prev_last_frame(self, shot: dict) -> str:
        if not self._use_prev_shot_last_frame or not self._prev_frame_service:
            return ""

        prev_shot = shot.get("prev_shot")
        current = shot["storyboard"]
        if not self._prev_frame_service.should_use_prev_frame(
            prev_shot, current, self._cross_scene_prev_frame,
        ):
            return ""

        prev_last = self._prev_frame_service.resolve_last_frame_path(
            prev_shot, current, self._cross_scene_prev_frame,
        ) or ""

        if prev_last or not prev_shot:
            return prev_last

        pending_id = self._prev_frame_service.find_prev_pending_provider_task_id(prev_shot.id)
        if pending_id:
            scene_number = prev_shot.scene_number
            shot_number = prev_shot.shot_number
            self.progress.emit(
                0, len(self._shot_list),
                f"等待上一镜完成 场{scene_number}镜{shot_number}...",
            )
            self._wait_for_task(pending_id)
            prev_last = self._prev_frame_service.resolve_last_frame_path(
                prev_shot, current, self._cross_scene_prev_frame,
            ) or ""

        return prev_last

    def _submit_shot(self, shot: dict, prev_last: str) -> str | None:
        params = self._build_params(shot)
        reference_images = shot.get("reference_images", [])
        return self._service.submit_shot_video(
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
            prev_shot_last_frame=prev_last,
        )

    def _run_serial_with_prev_frame(self) -> None:
        total = len(self._shot_list)
        for i, shot in enumerate(self._shot_list):
            if self._stopped:
                break

            scene_number = shot["scene_number"]
            shot_number = shot["shot_number"]
            self.progress.emit(i, total, f"准备场{scene_number}镜{shot_number}...")

            try:
                prev_last = self._resolve_prev_last_frame(shot)
                self.progress.emit(i, total, f"正在提交场{scene_number}镜{shot_number}...")
                provider_task_id = self._submit_shot(shot, prev_last)
                if not provider_task_id:
                    self._failed += 1
                    continue

                self.take_created.emit()
                self.progress.emit(i + 1, total, f"等待场{scene_number}镜{shot_number} 生成完成...")
                if self._wait_for_task(provider_task_id):
                    self._success += 1
                else:
                    self._failed += 1

                self.progress.emit(
                    i + 1, total,
                    f"已完成 {self._success}/{i + 1}，失败 {self._failed}",
                )
            except Exception:
                self._failed += 1
                self.progress.emit(i + 1, total, f"场{scene_number}镜{shot_number} 提交失败")

        if not self._stopped:
            self.all_done.emit(self._success, self._failed)
        else:
            self.terminated.emit(self._success, self._failed)

    def _run_parallel(self) -> None:
        self._signal_emitter.task_finished.connect(self._on_task_finished)
        self._signal_emitter.task_failed.connect(self._on_task_failed)

        submitted = 0
        for shot in self._shot_list:
            if self._stopped:
                break

            scene_number = shot["scene_number"]
            shot_number = shot["shot_number"]

            self.progress.emit(submitted, len(self._shot_list), f"正在提交场{scene_number}镜{shot_number}...")

            try:
                provider_task_id = self._submit_shot(shot, "")
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

    def _wait_for_task(self, provider_task_id: str) -> bool:
        if not provider_task_id:
            return False

        if self._prev_frame_service:
            outcome = self._prev_frame_service.get_provider_task_outcome(provider_task_id)
            if outcome is not None:
                finished, success = outcome
                if finished:
                    return success

        event = threading.Event()
        result = {"success": False}

        def on_finished(task_id: str, _save_path: str, _storyboard_id: int = 0) -> None:
            if task_id == provider_task_id:
                result["success"] = True
                event.set()

        def on_failed(task_id: str, _error: str) -> None:
            if task_id == provider_task_id:
                result["success"] = False
                event.set()

        self._signal_emitter.task_finished.connect(on_finished)
        self._signal_emitter.task_failed.connect(on_failed)
        try:
            while not event.is_set() and not self._stopped:
                event.wait(timeout=0.5)
        finally:
            try:
                self._signal_emitter.task_finished.disconnect(on_finished)
                self._signal_emitter.task_failed.disconnect(on_failed)
            except RuntimeError:
                pass

        return result["success"] and not self._stopped

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
