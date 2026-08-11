from __future__ import annotations

import json

from PySide6.QtCore import QObject, Property, Signal, Slot

from bridge.models.storyboard_model import StoryboardListModel
from bridge.workers import (
    DesignImageWorker, BatchDesignImageWorker, BatchGenerationController,
    StoryboardGenerateWorker, StoryboardOptimizeWorker,
)
from utils.path_converter import to_absolute_path
from prompts.video_prompt_builder import VideoPromptBuilder


class StoryboardBridge(QObject):
    data_changed = Signal()
    design_image_ready = Signal(str, str)  # shot_id, image_path
    design_image_progress = Signal(str)
    design_image_failed = Signal(str)
    batch_progress = Signal(int, int, str)
    batch_done = Signal(int, int)
    shot_detail_changed = Signal()
    shot_saved = Signal()
    shot_deleted = Signal()
    storyboard_generated = Signal(int)  # shot_count
    storyboard_optimized = Signal(int)  # shot_count
    storyboard_generation_failed = Signal(str)
    isOptimizingChanged = Signal()
    bridge_error = Signal(str)

    _SHOT_SIZE_INDEX_MAP = {
        0: "extreme_close_up", 1: "close_up", 2: "medium_shot",
        3: "full_shot", 4: "long_shot", 5: "extreme_long_shot",
    }
    _SHOT_SIZE_REVERSE = {
        "extreme_close_up": 0, "close_up": 1, "medium_shot": 2,
        "full_shot": 3, "long_shot": 4, "extreme_long_shot": 5,
    }

    def __init__(
        self, storyboard_service, screenplay_service,
        text_model_service, image_service, character_service,
        media_service, story_outline_service, project_service,
        visual_style_service, container, parent=None,
    ):
        super().__init__(parent)
        self._storyboard_service = storyboard_service
        self._screenplay_service = screenplay_service
        self._text_model_service = text_model_service
        self._image_service = image_service
        self._character_service = character_service
        self._media_service = media_service
        self._story_outline_service = story_outline_service
        self._project_service = project_service
        self._visual_style_service = visual_style_service
        self._container = container
        self._model = StoryboardListModel(
            workspace_root=container.config.workspace_root(), parent=self,
        )
        self._workers = []
        self._optimizing = False
        self._optimize_worker = None
        self._generate_worker = None
        self._project_id: int = -1
        self._cur_shot_id: int = -1
        self._cur_scene_number: int = 0
        self._cur_shot_number: int = 0
        self._cur_shot_size_index: int = 2
        self._cur_camera_movement: str = ""
        self._cur_content: str = ""
        self._cur_sound_effect: str = ""
        self._cur_ambient_sound: str = ""
        self._cur_background_music: str = ""
        self._cur_duration: float = 5.0
        self._cur_notes: str = ""
        self._cur_design_image: str = ""
        self._cur_seed: str = ""

    def _get_project_name(self, project_id: int | None = None) -> str | None:
        pid = project_id if project_id is not None else self._project_id
        if self._project_service and pid >= 0:
            project = self._project_service.get_project(project_id=pid)
            return project.name if project else None
        return None

    @Property(QObject, constant=True)
    def model(self):
        return self._model

    @Property(int, notify=shot_detail_changed)
    def curShotId(self): return self._cur_shot_id

    @Property(int, notify=shot_detail_changed)
    def curSceneNumber(self): return self._cur_scene_number

    @Property(int, notify=shot_detail_changed)
    def curShotNumber(self): return self._cur_shot_number

    @Property(int, notify=shot_detail_changed)
    def curShotSizeIndex(self): return self._cur_shot_size_index

    @Property(str, notify=shot_detail_changed)
    def curCameraMovement(self): return self._cur_camera_movement

    @Property(str, notify=shot_detail_changed)
    def curVisualContent(self): return self._cur_content

    @Property(str, notify=shot_detail_changed)
    def curSoundEffect(self): return self._cur_sound_effect

    @Property(str, notify=shot_detail_changed)
    def curAmbientSound(self): return self._cur_ambient_sound

    @Property(str, notify=shot_detail_changed)
    def curBackgroundMusic(self): return self._cur_background_music

    @Property(float, notify=shot_detail_changed)
    def curDuration(self): return self._cur_duration

    @Property(str, notify=shot_detail_changed)
    def curNotes(self): return self._cur_notes

    @Property(str, notify=shot_detail_changed)
    def curDesignImage(self): return self._cur_design_image

    @Property(str, notify=shot_detail_changed)
    def curSeed(self): return self._cur_seed

    @Property(bool, notify=isOptimizingChanged)
    def isOptimizing(self): return self._optimizing

    @Slot(int)
    def load_for_project(self, project_id: int) -> None:
        self._project_id = project_id
        shots = self._storyboard_service.list_storyboards(project_id=project_id)
        self._model.reset(shots)

    @Slot(int)
    def generate_from_screenplay(self, project_id: int) -> None:
        self._project_id = project_id

        try:
            scenes = self._screenplay_service.list_scenes(project_id=project_id)
            if not scenes:
                self.bridge_error.emit("该项目还没有剧本场次，请先生成剧本")
                return

            script_lines = []
            for scene in scenes:
                location_type_map = {
                    "interior": "内景",
                    "exterior": "外景",
                    "interior_exterior": "内景/外景"
                }
                time_type_map = {
                    "day": "日",
                    "night": "夜",
                    "dawn": "晨",
                    "dusk": "黄昏",
                    "evening": "傍晚"
                }
                loc_type = location_type_map.get(scene.location_type.value, "内景")
                time_type = time_type_map.get(scene.time_type.value, "日")

                script_lines.append(f"第{scene.scene_number}场 {loc_type} {scene.location} {time_type}")
                script_lines.append(scene.content)
                script_lines.append("")

            script_content = "\n".join(script_lines)

            worker = StoryboardGenerateWorker(
                text_service=self._text_model_service, script_content=script_content,
                project_id=project_id,
                project_name=self._get_project_name(project_id),
            )

            def on_finished(result: dict) -> None:
                try:
                    shots_data = result.get("shots", [])
                    if not shots_data:
                        self.storyboard_generation_failed.emit("AI 返回的分镜数据为空")
                        return

                    scene_map = {scene.scene_number: scene.id for scene in scenes}

                    from models.enums import ShotSize
                    shot_size_map = {
                        "特写": ShotSize.CLOSE_UP,
                        "近景": ShotSize.CLOSE_UP,
                        "中景": ShotSize.MEDIUM_SHOT,
                        "全景": ShotSize.FULL_SHOT,
                        "远景": ShotSize.LONG_SHOT,
                        "极近特写": ShotSize.EXTREME_CLOSE_UP,
                        "大远景": ShotSize.EXTREME_LONG_SHOT,
                    }

                    for shot_dict in shots_data:
                        scene_number = shot_dict.get("scene_number", 1)
                        scene_id = scene_map.get(scene_number)

                        if not scene_id:
                            continue

                        shot_size_str = shot_dict.get("shot_size", "中景")
                        shot_size = shot_size_map.get(shot_size_str, ShotSize.MEDIUM_SHOT)

                        self._storyboard_service.create_storyboard(
                            scene_id=scene_id,
                            scene_number=scene_number,
                            shot_number=shot_dict.get("shot_number", 1),
                            shot_size=shot_size,
                            camera_movement=shot_dict.get("camera_movement", ""),
                            content=shot_dict.get("content", ""),
                            sound_effect=shot_dict.get("sound_effect", ""),
                            ambient_sound=shot_dict.get("ambient_sound", ""),
                            background_music=shot_dict.get("background_music", ""),
                            duration=float(shot_dict.get("duration", 5.0)),
                            notes=shot_dict.get("notes", ""),
                        )

                    self.load_for_project(project_id)
                    self.storyboard_generated.emit(len(shots_data))

                except Exception as e:
                    error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
                    self.storyboard_generation_failed.emit(error_msg)

            def on_failed(err: str) -> None:
                self.storyboard_generation_failed.emit(err)

            worker.finished.connect(on_finished)
            worker.failed.connect(on_failed)
            worker.finished.connect(worker.deleteLater)
            self._workers.append(worker)
            worker.start()

        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            self.bridge_error.emit(error_msg)

    @Slot(int)
    def load_shot(self, shot_id: int) -> None:
        try:
            shot = self._storyboard_service.get_storyboard(shot_id)
            if not shot:
                self.bridge_error.emit("分镜不存在")
                return
            self._cur_shot_id = shot.id
            self._cur_scene_number = shot.scene_number
            self._cur_shot_number = shot.shot_number
            self._cur_shot_size_index = self._SHOT_SIZE_REVERSE.get(shot.shot_size.value, 2)
            self._cur_camera_movement = shot.camera_movement
            self._cur_content = shot.content
            self._cur_sound_effect = shot.sound_effect
            self._cur_ambient_sound = shot.ambient_sound
            self._cur_background_music = shot.background_music
            self._cur_duration = shot.duration
            self._cur_notes = shot.notes
            self._cur_design_image = shot.design_image
            self._cur_seed = shot.seed
            self.shot_detail_changed.emit()
        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            self.bridge_error.emit(error_msg)

    @Slot(int, int, str, str, float, str, str, str, str, str, str)
    def save_shot(
        self, shot_id: int, shot_size_index: int, camera_movement: str,
        content: str, duration: float, sound_effect: str,
        ambient_sound: str, background_music: str, notes: str,
        design_image: str, seed: str,
    ) -> None:
        from models.enums import ShotSize
        shot_size_str = self._SHOT_SIZE_INDEX_MAP.get(shot_size_index, "medium_shot")
        try:
            ss = ShotSize(shot_size_str)
        except ValueError:
            ss = ShotSize.MEDIUM_SHOT
        try:
            self._storyboard_service.update_storyboard(
                storyboard_id=shot_id, shot_size=ss,
                camera_movement=camera_movement, content=content,
                duration=duration, sound_effect=sound_effect,
                ambient_sound=ambient_sound, background_music=background_music,
                notes=notes, design_image=design_image, seed=seed,
            )
            self.shot_saved.emit()
            if self._project_id >= 0:
                self.load_for_project(self._project_id)
        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            self.bridge_error.emit(error_msg)

    @Slot(int)
    def delete_shot(self, shot_id: int) -> None:
        try:
            self._storyboard_service.delete_storyboard(storyboard_id=shot_id)
            self.shot_deleted.emit()
            if self._project_id >= 0:
                self.load_for_project(self._project_id)
        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            self.bridge_error.emit(error_msg)

    @Slot(int, str, str, str, float, str, str, str)
    def update_shot(self, shot_id: int, shot_size: str, camera_movement: str,
                    content: str, duration: float, sound_effect: str,
                    ambient_sound: str, background_music: str) -> None:
        from models.enums import ShotSize
        try:
            ss = ShotSize(shot_size)
        except ValueError:
            ss = ShotSize.MEDIUM_SHOT
        self._storyboard_service.update_storyboard(
            storyboard_id=shot_id,
            shot_size=ss, camera_movement=camera_movement,
            content=content, duration=duration,
            sound_effect=sound_effect, ambient_sound=ambient_sound,
            background_music=background_music,
        )
        self.data_changed.emit()

    @Slot(int, int, int, str, int, str, str, str)
    def generate_video(self, shot_id: int, scene_number: int, shot_number: int,
                       prompt: str, project_id: int, design_image: str,
                       provider_name: str, model_name: str) -> None:
        self.data_changed.emit()

    @Slot(int, int)
    def generate_design_image(self, storyboard_id: int, project_id: int) -> None:
        try:
            if storyboard_id <= 0:
                error_msg = f"无效的分镜 ID: {storyboard_id}"
                self.bridge_error.emit(error_msg)
                return

            if project_id <= 0:
                error_msg = f"无效的项目 ID: {project_id}"
                self.bridge_error.emit(error_msg)
                return

            storyboard = self._storyboard_service.get_storyboard(storyboard_id=storyboard_id)
            if not storyboard:
                self.bridge_error.emit(f"分镜不存在：{storyboard_id}")
                return

            if not storyboard.content or not storyboard.content.strip():
                self.bridge_error.emit("该分镜没有画面内容描述，无法生成设计图")
                return

            characters = self._character_service.list_characters(project_id=project_id)
            matched = [c for c in characters if c.name in storyboard.content or c.ref_code in storyboard.content]
            char_info = ""
            if matched:
                parts = []
                for c in matched:
                    traits = self._character_service.extract_fixed_traits(c.description)
                    if traits:
                        parts.append(f"{c.name}（{c.ref_code}）：{traits}")
                char_info = "\n".join(parts)

            shot_size_map = {
                "extreme_close_up": "特写", "close_up": "近景", "medium_shot": "中景",
                "full_shot": "全景", "long_shot": "远景", "extreme_long_shot": "大远景",
            }
            shot_size_text = shot_size_map.get(storyboard.shot_size.value, "中景")

            visual_style = ""
            if self._visual_style_service:
                project = self._project_service.get_project(project_id=project_id)
                if project:
                    style_id = project.visual_style_id
                    if not style_id:
                        default_style = self._visual_style_service.get_default_style()
                        if default_style:
                            style_id = default_style.id

                    if style_id:
                        style = self._visual_style_service.get_style(style_id)
                        if style:
                            visual_style = style.name

            worker = DesignImageWorker(
                text_service=self._text_model_service, image_service=self._image_service,
                storyboard_service=self._storyboard_service, storyboard=storyboard, shot_size_text=shot_size_text,
                character_info=char_info, project_id=project_id, visual_style=visual_style,
                project_name=self._get_project_name(project_id),
                config_manager=self._container.config_manager(),
                session_manager=self._container.session_manager(),
                ai_request_logger=self._container.ai_request_logger(),
            )
            worker.finished.connect(lambda path: self._on_design_done(storyboard_id, path))
            worker.failed.connect(self.design_image_failed.emit)
            worker.progress_update.connect(self.design_image_progress.emit)
            worker.start()
            self._workers.append(worker)

        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            self.bridge_error.emit(error_msg)

    @Slot(int, str)
    def batch_generate_design_images(self, project_id: int, shot_ids_json: str) -> None:
        try:
            shots = self._storyboard_service.list_storyboards(project_id=project_id)
            if not shots:
                self.bridge_error.emit("没有分镜可以生成设计图")
                return

            if shot_ids_json and shot_ids_json != "[]":
                try:
                    selected_ids = json.loads(shot_ids_json)
                except (json.JSONDecodeError, TypeError):
                    self.bridge_error.emit(f"参数解析失败")
                    return

                shots = [s for s in shots if s.id in selected_ids]
                if not shots:
                    self.bridge_error.emit("未找到选中的分镜")
                    return

            shot_list = []
            for shot in shots:
                shot_list.append({
                    "storyboard_id": shot.id,
                    "project_id": project_id,
                    "scene_number": shot.scene_number,
                    "shot_number": shot.shot_number,
                    "content": shot.content,
                    "shot_size": shot.shot_size,
                    "camera_movement": shot.camera_movement,
                    "sound_effect": shot.sound_effect,
                    "ambient_sound": shot.ambient_sound,
                    "background_music": shot.background_music,
                    "notes": shot.notes,
                })

            visual_style = ""
            if self._visual_style_service:
                project = self._project_service.get_project(project_id=project_id)
                if project:
                    style_id = project.visual_style_id
                    if not style_id:
                        default_style = self._visual_style_service.get_default_style()
                        if default_style:
                            style_id = default_style.id

                    if style_id:
                        style = self._visual_style_service.get_style(style_id)
                        if style:
                            visual_style = style.name

            worker = BatchDesignImageWorker(
                text_service=self._text_model_service,
                image_service=self._image_service,
                storyboard_service=self._storyboard_service,
                character_service=self._character_service,
                shot_list=shot_list,
                visual_style=visual_style,
                project_name=self._get_project_name(project_id),
                config_manager=self._container.config_manager(),
                session_manager=self._container.session_manager(),
                ai_request_logger=self._container.ai_request_logger(),
            )

            def on_progress(current: int, message: str, count_info: str) -> None:
                self.batch_progress.emit(current, len(shot_list), message)

            def on_finished(success_count: int, total: int) -> None:
                self.batch_done.emit(success_count, total)
                self.load_for_project(project_id)

            def on_shot_design_done(shot_id: int, path: str) -> None:
                self._model.update_design_image(shot_id, path)
                if self._cur_shot_id == shot_id:
                    self._cur_design_image = path
                    self.shot_detail_changed.emit()
                self.design_image_ready.emit(str(shot_id), path)

            worker.progress_update.connect(on_progress)
            worker.shot_design_done.connect(on_shot_design_done)
            worker.finished.connect(on_finished)
            worker.failed.connect(self.design_image_failed.emit)
            worker.finished.connect(worker.deleteLater)
            self._workers.append(worker)
            worker.start()

        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            self.bridge_error.emit(error_msg)

    @Slot(int, str)
    def batch_generate_videos(self, project_id: int, shot_ids_json: str) -> None:
        try:
            selected_ids = json.loads(shot_ids_json) if shot_ids_json else []
            if not selected_ids:
                self.bridge_error.emit("未选中任何分镜")
                return

            shots = self._storyboard_service.list_storyboards(project_id=project_id)
            selected_shots = [s for s in shots if s.id in selected_ids]
            if not selected_shots:
                self.bridge_error.emit("未找到选中的分镜")
                return

            scenes = self._screenplay_service.list_scenes(project_id=project_id)
            scene_map = {s.id: s for s in scenes}

            characters = self._character_service.list_characters(project_id=project_id)
            workspace_root = self._container.config.workspace_root()

            project = self._project_service.get_project(project_id=project_id)
            if not project:
                self.bridge_error.emit("项目不存在")
                return

            visual_style_name = None
            if project.visual_style_id:
                visual_style = self._visual_style_service.get_style(project.visual_style_id)
                if visual_style:
                    visual_style_name = visual_style.name

            if not visual_style_name:
                default_style = self._visual_style_service.get_default_style()
                if default_style:
                    visual_style_name = default_style.name

            shot_list_for_prompt = [s for s in shots]
            shot_list = []
            for i, shot in enumerate(selected_shots):
                scene = scene_map.get(shot.scene_id)
                idx = next((j for j, s in enumerate(shot_list_for_prompt) if s.id == shot.id), -1)
                prev_shot = shot_list_for_prompt[idx - 1] if idx > 0 else None
                next_shot = shot_list_for_prompt[idx + 1] if idx < len(shot_list_for_prompt) - 1 else None

                reference_images_paths = []
                reference_images_info = []

                if shot.design_image:
                    abs_path = to_absolute_path(shot.design_image, workspace_root)
                    if abs_path:
                        reference_images_paths.append(abs_path)
                        reference_images_info.append({
                            "type": "design",
                            "description": ""
                        })

                content = shot.content or ""
                for c in characters:
                    if len(reference_images_paths) >= 5:
                        break
                    if c.design_image and (c.name in content or c.ref_code in content):
                        abs_path = to_absolute_path(c.design_image, workspace_root)
                        if abs_path:
                            reference_images_paths.append(abs_path)
                            reference_images_info.append({
                                "type": "character",
                                "character_name": c.name,
                                "description": ""
                            })

                chat_service = self._container.chat_model_service()
                template_manager = self._container.prompt_template_manager()

                prompt = VideoPromptBuilder.build_shot_prompt(
                    shot, scene, prev_shot, next_shot,
                    reference_images=reference_images_info,
                    visual_style=visual_style_name,
                    clean_dialogue_and_sound=True,
                    chat_service=chat_service,
                    template_manager=template_manager,
                )

                shot_list.append({
                    "scene_number": shot.scene_number,
                    "shot_number": shot.shot_number,
                    "prompt": prompt,
                    "project_id": project_id,
                    "shot_id": shot.id,
                    "reference_images": reference_images_paths,
                    "duration": shot.duration if shot.duration > 0 else None,
                })

            config_mgr = self._container.config_manager()
            settings = config_mgr.settings
            provider_name = settings.default_provider
            if not provider_name:
                self.bridge_error.emit("未配置默认视频生成供应商")
                return

            provider_cfg = config_mgr.get_provider_config(name=provider_name, provider_type="video")

            signal_emitter = self._container.video_polling_task().signal_emitter
            video_service = self._container.video_service()

            controller = BatchGenerationController(
                shot_list=shot_list, video_service=video_service, signal_emitter=signal_emitter,
                provider_name=provider_name, project=project, provider_cfg=provider_cfg,
            )

            def on_progress(current: int, total: int, message: str) -> None:
                self.batch_progress.emit(current, total, message)

            def on_all_done(success: int, failed: int) -> None:
                self.batch_done.emit(success, failed)
                controller.deleteLater()

            def on_terminated(success: int, failed: int) -> None:
                self.batch_done.emit(success, failed)
                controller.deleteLater()

            controller.progress.connect(on_progress)
            controller.all_done.connect(on_all_done)
            controller.terminated.connect(on_terminated)
            controller.start()

        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            self.bridge_error.emit(error_msg)

    @Slot(int, str)
    def upload_design_image(self, shot_id: int, image_path: str) -> None:
        """上传/替换设计图。"""
        try:
            self._storyboard_service.update_storyboard(
                storyboard_id=shot_id, design_image=image_path,
            )
            self._model.update_design_image(shot_id, image_path)
            if self._cur_shot_id == shot_id:
                self._cur_design_image = image_path
                self.shot_detail_changed.emit()
            self.design_image_ready.emit(str(shot_id), image_path)
        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            self.bridge_error.emit(error_msg)

    @Slot(int)
    def delete_design_image(self, shot_id: int) -> None:
        """删除分镜的设计图。"""
        try:
            self._storyboard_service.update_storyboard(
                storyboard_id=shot_id, design_image="",
            )
            self._model.update_design_image(shot_id, "")
            if self._cur_shot_id == shot_id:
                self._cur_design_image = ""
                self.shot_detail_changed.emit()
        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            self.bridge_error.emit(error_msg)

    @Slot(int, result=str)
    def get_related_videos(self, shot_id: int) -> str:
        try:
            videos = self._media_service.list_by_storyboard(storyboard_id=shot_id)
            result = []
            for v in videos:
                result.append({
                    "fileId": v.id,
                    "fileName": v.filename,
                    "filePath": v.local_path,
                    "thumbnailPath": v.thumbnail_path or "",
                    "duration": v.duration,
                    "width": v.width,
                    "height": v.height,
                    "featured": getattr(v, "featured", False),
                })
            return json.dumps(result)
        except Exception:
            return "[]"

    def _on_design_done(self, shot_id: int, path: str) -> None:
        self._model.update_design_image(shot_id, path)
        if self._cur_shot_id == shot_id:
            self._cur_design_image = path
            self.shot_detail_changed.emit()
        self.design_image_ready.emit(str(shot_id), path)

    @Slot(str, int)
    def optimize_with_ai(self, user_input: str, project_id: int) -> None:
        """AI 优化分镜：自动判断生成或优化"""
        if self._optimizing:
            return

        try:
            # 1. 获取大纲、剧本、角色
            outline = self._story_outline_service.get_or_create_story_outline(project_id=project_id)
            scenes = self._screenplay_service.list_scenes(project_id=project_id)
            characters = self._character_service.list_characters(project_id=project_id)

            has_content = bool(outline.content and outline.content.strip())
            has_scenes = bool(scenes)

            if not has_content or not has_scenes:
                error_msg = "必须先完成大纲和剧本"
                self.bridge_error.emit(error_msg)
                return

            # 2. 查询现有分镜
            storyboards = self._storyboard_service.list_storyboards(project_id=project_id)

            # 3. 判断分支
            if not storyboards:
                self._generate_storyboard_with_requirement(outline.content, scenes, characters, user_input, project_id)
            else:
                self._optimize_storyboard(outline.content, scenes, characters, storyboards, user_input, project_id)

        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            self.bridge_error.emit(error_msg)

    def _generate_storyboard_with_requirement(self, outline_content: str, scenes: list, characters: list, user_input: str, project_id: int) -> None:
        script_content = self._format_script_as_text(scenes)
        character_content = self._format_characters_as_text(characters)

        combined_requirement = f"用户要求：{user_input}\n\n大纲参考：{outline_content}"

        self._generate_worker = StoryboardGenerateWorker(
            text_service=self._text_model_service, script_content=script_content, art_style=combined_requirement,
            project_id=project_id,
            project_name=self._get_project_name(project_id),
        )

        def on_finished(result: list) -> None:
            try:
                shots_data = result

                if not shots_data:
                    self.storyboard_generation_failed.emit("AI 返回的分镜数据为空")
                    return

                scene_map = {s.scene_number: s.id for s in scenes}

                storyboards = []
                for shot_data in shots_data:
                    scene_number = shot_data.get("scene_number", 1)
                    scene_id = scene_map.get(scene_number, 0)

                    from models.storyboard import Storyboard
                    from models.enums import ShotSize

                    shot_size_map = {
                        "extreme_close_up": ShotSize.EXTREME_CLOSE_UP,
                        "close_up": ShotSize.CLOSE_UP,
                        "medium_shot": ShotSize.MEDIUM_SHOT,
                        "full_shot": ShotSize.FULL_SHOT,
                        "long_shot": ShotSize.LONG_SHOT,
                        "extreme_long_shot": ShotSize.EXTREME_LONG_SHOT,
                    }

                    shot_size = shot_size_map.get(shot_data.get("shot_size", "medium_shot"), ShotSize.MEDIUM_SHOT)

                    storyboard = Storyboard(
                        scene_id=scene_id,
                        scene_number=scene_number,
                        shot_number=shot_data.get("shot_number", 1),
                        shot_size=shot_size,
                        camera_movement=shot_data.get("camera_movement", ""),
                        content=shot_data.get("content", ""),
                        sound_effect=shot_data.get("sound_effect", ""),
                        ambient_sound=shot_data.get("ambient_sound", ""),
                        background_music=shot_data.get("background_music", ""),
                        duration=shot_data.get("duration", 5.0),
                        notes=shot_data.get("color_lighting", ""),
                    )
                    storyboards.append(storyboard)

                self._storyboard_service.batch_create_storyboards(storyboards=storyboards)

                self.load_for_project(project_id)
                self.storyboard_generated.emit(len(storyboards))

            except Exception as e:
                self.storyboard_generation_failed.emit(f"保存失败：{e}")

        def on_failed(err: str) -> None:
            self.storyboard_generation_failed.emit(err)

        self._generate_worker.finished.connect(on_finished)
        self._generate_worker.failed.connect(on_failed)
        self._generate_worker.finished.connect(self._generate_worker.deleteLater)
        self._generate_worker.start()

    def _optimize_storyboard(self, outline_content: str, scenes: list, characters: list, storyboards: list, user_input: str, project_id: int) -> None:
        self._optimizing = True
        self.isOptimizingChanged.emit()

        script_content = self._format_script_as_text(scenes)
        character_content = self._format_characters_as_text(characters)
        current_storyboard = self._format_storyboards_as_text(storyboards)

        self._optimize_worker = StoryboardOptimizeWorker(
            text_service=self._text_model_service,
            outline_content=outline_content,
            script_content=script_content,
            character_content=character_content,
            current_storyboard=current_storyboard,
            user_requirement=user_input,
            project_id=project_id,
            project_name=self._get_project_name(project_id),
        )

        def on_finished(new_shots: list) -> None:
            self._optimizing = False
            self.isOptimizingChanged.emit()
            try:
                for shot in storyboards:
                    self._storyboard_service.delete_storyboard(storyboard_id=shot.id)

                scene_map = {s.scene_number: s.id for s in scenes}

                storyboards_to_create = []
                for shot_data in new_shots:
                    scene_number = shot_data.get("scene_number", 1)
                    scene_id = scene_map.get(scene_number, 0)

                    from models.storyboard import Storyboard
                    from models.enums import ShotSize

                    shot_size_map = {
                        "extreme_close_up": ShotSize.EXTREME_CLOSE_UP,
                        "close_up": ShotSize.CLOSE_UP,
                        "medium_shot": ShotSize.MEDIUM_SHOT,
                        "full_shot": ShotSize.FULL_SHOT,
                        "long_shot": ShotSize.LONG_SHOT,
                        "extreme_long_shot": ShotSize.EXTREME_LONG_SHOT,
                    }

                    shot_size = shot_size_map.get(shot_data.get("shot_size", "medium_shot"), ShotSize.MEDIUM_SHOT)

                    storyboard = Storyboard(
                        scene_id=scene_id,
                        scene_number=scene_number,
                        shot_number=shot_data.get("shot_number", 1),
                        shot_size=shot_size,
                        camera_movement=shot_data.get("camera_movement", ""),
                        content=shot_data.get("content", ""),
                        sound_effect=shot_data.get("sound_effect", ""),
                        ambient_sound=shot_data.get("ambient_sound", ""),
                        background_music=shot_data.get("background_music", ""),
                        duration=shot_data.get("duration", 5.0),
                        notes=shot_data.get("color_lighting", ""),
                    )
                    storyboards_to_create.append(storyboard)

                self._storyboard_service.batch_create_storyboards(storyboards=storyboards_to_create)

                self.load_for_project(project_id)
                self.storyboard_optimized.emit(len(storyboards_to_create))

            except Exception as e:
                self.storyboard_generation_failed.emit(f"保存失败：{e}")

        def on_failed(err: str) -> None:
            self._optimizing = False
            self.isOptimizingChanged.emit()
            self.storyboard_generation_failed.emit(f"优化分镜失败：{err}")

        self._optimize_worker.finished.connect(on_finished)
        self._optimize_worker.failed.connect(on_failed)
        self._optimize_worker.finished.connect(self._optimize_worker.deleteLater)
        self._optimize_worker.start()

    def _format_script_as_text(self, scenes: list) -> str:
        """将场次列表格式化为文本"""
        lines = []
        for scene in scenes:
            location_type_map = {
                "interior": "内景",
                "exterior": "外景",
                "interior_exterior": "内景/外景"
            }
            time_type_map = {
                "day": "日",
                "night": "夜",
                "dawn": "晨",
                "dusk": "黄昏",
                "evening": "傍晚"
            }
            loc_type = location_type_map.get(scene.location_type.value, "内景")
            time_type = time_type_map.get(scene.time_type.value, "日")

            lines.append(f"第{scene.scene_number}场 {loc_type} {scene.location} {time_type}")
            lines.append(scene.content)
            lines.append("")

        return "\n".join(lines)

    def _format_characters_as_text(self, characters: list) -> str:
        """将角色列表格式化为文本"""
        if not characters:
            return "（无角色设计）"

        lines = []
        for char in characters:
            lines.append(f"【{char.name}】（{char.ref_code}）")
            lines.append(char.description)
            lines.append("")

        return "\n".join(lines)

    def _format_storyboards_as_text(self, storyboards: list) -> str:
        """将分镜列表格式化为 Markdown 表格"""
        lines = [
            "| 场次 | 镜头序号 | 景别 | 画面内容描述 | 运镜方式 | 音效 | 环境音 | 背景音乐 | 时长(秒) | 色调/光影 |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ]

        shot_size_map = {
            "extreme_close_up": "极近特写",
            "close_up": "特写",
            "medium_shot": "中景",
            "full_shot": "全景",
            "long_shot": "远景",
            "extreme_long_shot": "大远景",
        }

        for shot in storyboards:
            shot_size = shot_size_map.get(shot.shot_size, "中景")
            sound_effect = shot.sound_effect or "无"
            ambient_sound = shot.ambient_sound or "无"
            background_music = shot.background_music or "无"

            lines.append(
                f"| {shot.scene_number} | {shot.shot_number} | {shot_size} | "
                f"{shot.content} | {shot.camera_movement} | {sound_effect} | "
                f"{ambient_sound} | {background_music} | {shot.duration} | {shot.notes or '无'} |"
            )

        return "\n".join(lines)
