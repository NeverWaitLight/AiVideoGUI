from __future__ import annotations

import os
from loguru import logger
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, QThread, Signal

if TYPE_CHECKING:
    from di import ApplicationContainer

from utils import paths


class ScriptGenerateWorker(QThread):
    finished = Signal(str, list)
    failed = Signal(str)

    def __init__(self, text_service, outline_content: str, parent=None):
        super().__init__(parent)
        self._text_service = text_service
        self._outline_content = outline_content

    def run(self):
        try:
            title, scenes = self._text_service.generate_script(self._outline_content)
            self.finished.emit(title, scenes)
        except Exception as e:
            logger.exception("生成剧本失败")
            self.failed.emit(str(e))


class StoryboardGenerateWorker(QThread):
    finished = Signal(dict)
    failed = Signal(str)

    def __init__(self, text_service, script_content: str, art_style: str = "", parent=None):
        super().__init__(parent)
        self._text_service = text_service
        self._script_content = script_content
        self._art_style = art_style

    def run(self):
        try:
            result = self._text_service.generate_storyboard(self._script_content, self._art_style)
            self.finished.emit(result)
        except Exception as e:
            logger.exception("生成分镜失败")
            self.failed.emit(str(e))


class CharacterWorker(QThread):
    finished = Signal(list)
    failed = Signal(str)

    def __init__(self, text_service, mode: str, **kwargs):
        super().__init__()
        self._text_service = text_service
        self._mode = mode
        self._kwargs = kwargs

    def run(self):
        try:
            if self._mode == 'generate':
                characters = self._text_service.generate_characters(
                    outline_content=self._kwargs['outline_content'],
                    script_content=self._kwargs['script_content'],
                    user_requirement=self._kwargs['user_requirement'],
                )
            else:
                characters = self._text_service.optimize_characters(
                    outline_content=self._kwargs['outline_content'],
                    script_content=self._kwargs['script_content'],
                    current_characters=self._kwargs['current_characters'],
                    user_requirement=self._kwargs['user_requirement'],
                )
            self.finished.emit(characters)
        except Exception as e:
            logger.exception(f"{'生成' if self._mode == 'generate' else '优化'}角色失败")
            self.failed.emit(str(e))


class ScreenplayOptimizeWorker(QThread):
    finished = Signal(str, list)
    failed = Signal(str)

    def __init__(self, text_service, outline_content: str, current_script: str, user_requirement: str, parent=None):
        super().__init__(parent)
        self._text_service = text_service
        self._outline_content = outline_content
        self._current_script = current_script
        self._user_requirement = user_requirement

    def run(self):
        try:
            title, scenes = self._text_service.optimize_screenplay(
                self._outline_content,
                self._current_script,
                self._user_requirement,
            )
            self.finished.emit(title, scenes)
        except Exception as e:
            logger.exception("优化剧本失败")
            self.failed.emit(str(e))


class StoryboardOptimizeWorker(QThread):
    finished = Signal(list)
    failed = Signal(str)

    def __init__(self, text_service, outline_content: str, script_content: str,
                 character_content: str, current_storyboard: str, user_requirement: str, parent=None):
        super().__init__(parent)
        self._text_service = text_service
        self._outline_content = outline_content
        self._script_content = script_content
        self._character_content = character_content
        self._current_storyboard = current_storyboard
        self._user_requirement = user_requirement

    def run(self):
        try:
            shots = self._text_service.optimize_storyboard(
                self._outline_content,
                self._script_content,
                self._character_content,
                self._current_storyboard,
                self._user_requirement,
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
        parent=None,
    ):
        super().__init__(parent)
        self._text_service = text_service
        self._image_service = image_service
        self._storyboard_service = storyboard_service
        self._storyboard = storyboard
        self._shot_size_text = shot_size_text
        self._character_info = character_info
        self._project_id = project_id

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
            )
            logger.info(f"设计图提示词：{image_prompt}")

            self.progress_update.emit("正在调用图片生成模型...")
            save_path = os.path.join(
                paths.projects_dir(paths.workspace_root()),
                str(self._project_id),
                f"design-{self._storyboard.scene_number}-{self._storyboard.shot_number}.png",
            )
            result_path = self._image_service.generate(prompt=image_prompt, save_path=save_path)

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
    finished = Signal(int, int)
    failed = Signal(str)

    def __init__(
        self, text_service, image_service, storyboard_service, character_service,
        shot_list: list[dict], parent=None,
    ):
        super().__init__(parent)
        self._text_service = text_service
        self._image_service = image_service
        self._storyboard_service = storyboard_service
        self._character_service = character_service
        self._shot_list = shot_list

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
                )

                save_path = os.path.join(
                    paths.projects_dir(paths.workspace_root()),
                    str(project_id),
                    f"design-{scene_number}-{shot_number}.png",
                )
                result_path = self._image_service.generate(prompt=image_prompt, save_path=save_path)

                self._storyboard_service.update_storyboard(
                    storyboard_id=storyboard_id, design_image=result_path,
                )
                success_count += 1
                self.progress_update.emit(idx, f"完成 {scene_number}-{shot_number}", f"({idx}/{total})")

            except Exception as e:
                logger.warning(f"批量设计图生成 [{idx}/{total}] 失败：{e}")
                self.progress_update.emit(idx, f"失败：{e}", f"({idx}/{total})")

        self.finished.emit(success_count, total)


class CharacterDesignImageWorker(QThread):
    finished = Signal(str)
    failed = Signal(str)
    progress_update = Signal(str)

    def __init__(self, text_service, image_service, character_service, character, project_id: int, parent=None):
        super().__init__(parent)
        self._text_service = text_service
        self._image_service = image_service
        self._character_service = character_service
        self._character = character
        self._project_id = project_id

    def run(self):
        try:
            self.progress_update.emit("正在生成角色设计图提示词...")
            image_prompt = self._text_service.generate_character_design_image_prompt(
                character_name=self._character.name,
                description=self._character.description,
            )
            logger.info(f"角色设计图提示词：{image_prompt}")

            self.progress_update.emit("正在调用图片生成模型...")
            save_path = os.path.join(
                paths.projects_dir(paths.workspace_root()),
                str(self._project_id),
                f"char-{self._character.uuid}.png",
            )
            result_path = self._image_service.generate(prompt=image_prompt, save_path=save_path)

            self._character_service.update_character(
                character_uuid=self._character.uuid, design_image=result_path,
            )
            logger.info(f"角色设计图生成完成：{result_path}")
            self.finished.emit(result_path)
        except Exception as e:
            logger.exception("生成角色设计图失败")
            self.failed.emit(str(e))


class OptimizeWorker(QThread):
    finished = Signal(str)
    failed = Signal(str)

    def __init__(self, text_service, messages: list[dict], parent=None):
        super().__init__(parent)
        self._text_service = text_service
        self._messages = messages

    def run(self):
        try:
            reply = self._text_service.chat(self._messages)
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


class BatchGenerationController(QObject):
    progress = Signal(int, int, str)
    all_done = Signal(int, int)
    terminated = Signal(int, int)

    def __init__(
        self, shot_list: list[dict], container,
        provider_name: str, model_name: str, project, provider_cfg,
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self._shot_list = shot_list
        self._container = container
        self._service = container.video_service()
        self._polling = container.task_polling_service()
        self._provider_name = provider_name
        self._model_name = model_name
        self._project = project
        self._provider_cfg = provider_cfg
        self._success = 0
        self._failed = 0
        self._submitted_task_ids: set[str] = set()
        self._stopped = False

    def start(self) -> None:
        self._stopped = False
        self._polling.task_finished.connect(self._on_task_finished)
        self._polling.task_failed.connect(self._on_task_failed)

        submitted = 0
        for i, shot in enumerate(self._shot_list):
            if self._stopped:
                break

            scene_number = shot["scene_number"]
            shot_number = shot["shot_number"]
            prompt = shot["prompt"]
            project_id = shot["project_id"]
            shot_id = shot.get("shot_id", "")
            reference_image = shot.get("reference_image", "")

            self.progress.emit(submitted, len(self._shot_list), f"正在提交场{scene_number}镜{shot_number}...")

            try:
                conv_title = f"分镜视频-场{scene_number}镜{shot_number}"
                conv = self._service.create_conversation(
                    self._provider_name, self._model_name, conv_title,
                    project_id=project_id, is_hidden=True,
                )

                params = (self._provider_cfg.default_params if self._provider_cfg else {}).copy()
                params["resolution"] = self._project.resolution
                params["ratio"] = self._project.aspect_ratio

                seq = scene_number * 1000 + shot_number
                save_path = os.path.join(
                    paths.projects_dir(paths.workspace_root()),
                    str(project_id), f"{scene_number}-{shot_number}-{seq}.mp4",
                )

                msg = self._service.submit_task(
                    conversation_id=conv.id, prompt=prompt,
                    provider_name=self._provider_name, params=params,
                    save_path=save_path, storyboard_id=shot_id,
                    reference_image=reference_image,
                )
                self._submitted_task_ids.add(msg.task_id)
                submitted += 1
                mode_info = "(r2v)" if reference_image else "(t2v)"
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
            self._polling.task_finished.disconnect(self._on_task_finished)
            self._polling.task_failed.disconnect(self._on_task_failed)
        except RuntimeError:
            pass
        self.terminated.emit(self._success, self._failed)

    def _cleanup_and_finish(self) -> None:
        try:
            self._polling.task_finished.disconnect(self._on_task_finished)
            self._polling.task_failed.disconnect(self._on_task_failed)
        except RuntimeError:
            pass
        self.all_done.emit(self._success, self._failed)

    def _on_task_finished(self, message_id: str, local_path: str, storyboard_id: int = 0) -> None:
        from storage.session_manager import SessionManager
        msg_repo = self._container.session_manager().get_repo(MessageRepository)
        msg = msg_repo.get_by_id(message_id)
        if not msg or msg.task_id not in self._submitted_task_ids:
            return

        self._success += 1
        completed = self._success + self._failed
        total_submitted = len(self._submitted_task_ids)
        self.progress.emit(completed, total_submitted, f"已完成 {self._success}/{total_submitted}，失败 {self._failed}")

        if completed >= total_submitted:
            self._cleanup_and_finish()

    def _on_task_failed(self, message_id: str, error: str) -> None:
        msg_repo = self._container.session_manager().get_repo(MessageRepository)
        msg = msg_repo.get_by_id(message_id)
        if not msg or msg.task_id not in self._submitted_task_ids:
            return

        self._failed += 1
        completed = self._success + self._failed
        total_submitted = len(self._submitted_task_ids)
        self.progress.emit(completed, total_submitted, f"已完成 {self._success}/{total_submitted}，失败 {self._failed}")

        if completed >= total_submitted:
            self._cleanup_and_finish()
