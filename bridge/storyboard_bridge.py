from __future__ import annotations

import json

from PySide6.QtCore import QObject, Property, Signal, Slot

from bridge.models.storyboard_model import StoryboardListModel
from bridge.workers import (
    BatchGenerationController,
    StoryboardGenerateWorker, StoryboardOptimizeWorker,
)
from models.enums import GenerateTaskCallerType
from utils.path_converter import to_absolute_path


class StoryboardBridge(QObject):
    data_changed = Signal()
    design_image_ready = Signal(str, str)  # shot_id, image_path
    design_image_started = Signal(str)  # shot_id
    design_image_finished = Signal(str)  # shot_id
    design_image_progress = Signal(str)
    design_image_failed = Signal(str)
    video_generation_started = Signal(str)  # shot_id
    video_generation_finished = Signal(str)  # shot_id
    video_generation_failed = Signal(str, str)  # shot_id, error
    batch_progress = Signal(int, int, str)
    batch_done = Signal(int, int)
    shot_detail_changed = Signal()
    shot_saved = Signal()
    shot_deleted = Signal()
    storyboard_generated = Signal(int)  # shot_count
    storyboard_optimized = Signal(int)  # shot_count
    storyboard_generation_failed = Signal(str)
    isOptimizingChanged = Signal()
    generation_started = Signal()
    shot_added = Signal()
    takes_changed = Signal()
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
        visual_style_service, container, take_service=None, parent=None,
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
        self._take_service = take_service
        self._container = container
        self._model = StoryboardListModel(
            workspace_root=container.config.workspace_root(), parent=self,
        )
        self._workers = []
        self._optimizing = False
        self._optimize_worker = None
        self._generate_worker = None
        self._project_id: int = -1
        self._generation_snapshot: list = []
        self._created_ids: list[int] = []
        self._scene_map: dict[int, int] = {}
        self._generation_aborted: bool = False
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
        self._generating_design_shot_ids: set[int] = set()
        self._generating_video_shot_ids: set[int] = set()

        emitter = self._image_service.signal_emitter
        emitter.task_finished.connect(self._on_image_task_finished)
        emitter.task_failed.connect(self._on_image_task_failed)
        emitter.task_progress.connect(self._on_image_task_progress)

        video_service = self._container.video_service()
        video_emitter = video_service.signal_emitter
        video_emitter.take_created.connect(self.takes_changed.emit)
        video_emitter.video_generation_started.connect(self._on_video_generation_started)
        video_emitter.video_generation_failed.connect(self._on_video_generation_failed)
        polling_emitter = self._container.video_polling_task().signal_emitter
        polling_emitter.task_finished.connect(self._on_video_poll_finished)
        polling_emitter.task_failed.connect(self._on_video_poll_failed)

    def _on_image_task_finished(
        self, _provider_task_id: str, caller_type: str, caller_id: str, relative_path: str,
    ) -> None:
        if caller_type != GenerateTaskCallerType.STORYBOARD.value:
            return
        self._on_design_done(int(caller_id), relative_path)

    def _on_image_task_failed(
        self, _provider_task_id: str, caller_type: str, caller_id: str, error: str,
    ) -> None:
        if caller_type != GenerateTaskCallerType.STORYBOARD.value:
            return
        self._on_design_failed(int(caller_id), error)

    def _on_image_task_progress(self, _provider_task_id: str, message: str) -> None:
        self.design_image_progress.emit(message)

    def _build_character_info(self, project_id: int, content: str) -> str:
        characters = self._character_service.list_characters(project_id=project_id)
        matched = [c for c in characters if c.name in content or c.ref_code in content]
        if not matched:
            return ""
        parts = []
        for c in matched:
            traits = self._character_service.extract_fixed_traits(c.description)
            if traits:
                parts.append(f"{c.name}（{c.ref_code}）：{traits}")
        return "\n".join(parts)

    def _mark_design_generating(self, shot_id: int) -> None:
        self._generating_design_shot_ids.add(shot_id)
        self.design_image_started.emit(str(shot_id))

    def _unmark_design_generating(self, shot_id: int) -> None:
        if shot_id in self._generating_design_shot_ids:
            self._generating_design_shot_ids.discard(shot_id)
            self.design_image_finished.emit(str(shot_id))

    def _mark_video_generating(self, shot_id: int) -> None:
        self._generating_video_shot_ids.add(shot_id)
        self.video_generation_started.emit(str(shot_id))

    def _unmark_video_generating(self, shot_id: int) -> None:
        if shot_id in self._generating_video_shot_ids:
            self._generating_video_shot_ids.discard(shot_id)
            self.video_generation_finished.emit(str(shot_id))

    def _on_video_generation_started(self, shot_id: str) -> None:
        try:
            self._mark_video_generating(int(shot_id))
        except ValueError:
            pass
        self.takes_changed.emit()

    def _on_video_generation_failed(self, shot_id: str, error: str) -> None:
        try:
            self._unmark_video_generating(int(shot_id))
        except ValueError:
            pass
        self.video_generation_failed.emit(shot_id, error)
        self.takes_changed.emit()

    def _on_video_poll_finished(self, _provider_task_id: str, _save_path: str, storyboard_id: int) -> None:
        if storyboard_id > 0:
            self._unmark_video_generating(storyboard_id)
        self.takes_changed.emit()

    def _on_video_poll_failed(self, provider_task_id: str, error: str) -> None:
        from storage.repositories.generate_task_repository import GenerateTaskRepository

        task_repo = self._container.session_manager().get_repo(GenerateTaskRepository)
        task = task_repo.get_by_provider_task_id(provider_task_id)
        if task and task.get("caller_type") == GenerateTaskCallerType.STORYBOARD.value:
            try:
                shot_id = int(task.get("caller_id") or "0")
                if shot_id > 0:
                    self._unmark_video_generating(shot_id)
                    self.video_generation_failed.emit(str(shot_id), error)
            except ValueError:
                pass
        self.takes_changed.emit()

    def _build_video_request_for_shot(
        self,
        shot,
        project,
        *,
        provider_name: str,
        params: dict | None = None,
        reference_images: list[str] | None = None,
        reference_images_info: list[dict] | None = None,
        visual_style: str | None = None,
        prev_shot=None,
        next_shot=None,
        scene=None,
        prev_shot_last_frame: str = "",
    ):
        from models.video_generation_request import VideoGenerationRequest, VideoScene

        return VideoGenerationRequest(
            scene=VideoScene.SHOT_VIDEO,
            storyboard_id=shot.id,
            local_path="",
            provider_name=provider_name,
            project_id=project.id,
            project_name=project.name,
            scene_id=scene.id if scene else shot.scene_id,
            prev_shot_id=prev_shot.id if prev_shot else None,
            next_shot_id=next_shot.id if next_shot else None,
            scene_number=shot.scene_number,
            shot_number=shot.shot_number,
            reference_images=list(reference_images or []),
            reference_images_info=list(reference_images_info or []),
            visual_style=visual_style,
            params=dict(params or {}),
            prev_shot_last_frame=prev_shot_last_frame,
            clean_prompt=True,
        )

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
            workspace_root = self._container.config.workspace_root()
            self._cur_design_image = to_absolute_path(shot.design_image, workspace_root)
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
            # design_image 为空时保留库中已有路径，避免手动保存冲掉异步生成结果
            design_image_arg = design_image if design_image else None
            if design_image_arg is None and self._cur_shot_id == shot_id and self._cur_design_image:
                design_image_arg = self._cur_design_image
            self._storyboard_service.update_storyboard(
                storyboard_id=shot_id, shot_size=ss,
                camera_movement=camera_movement, content=content,
                duration=duration, sound_effect=sound_effect,
                ambient_sound=ambient_sound, background_music=background_music,
                notes=notes, design_image=design_image_arg, seed=seed,
            )
            if design_image_arg is not None and self._cur_shot_id == shot_id:
                workspace_root = self._container.config.workspace_root()
                self._cur_design_image = to_absolute_path(design_image_arg, workspace_root)
                self._model.update_design_image(shot_id, self._cur_design_image)
            self.shot_saved.emit()
            if self._project_id >= 0:
                self.load_for_project(self._project_id)
            if self._cur_shot_id == shot_id:
                self.load_shot(shot_id)
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
        try:
            if shot_id <= 0 or project_id <= 0:
                self.bridge_error.emit("无效的分镜或项目 ID")
                return

            storyboard = self._storyboard_service.get_storyboard(storyboard_id=shot_id)
            if not storyboard:
                self.bridge_error.emit(f"分镜不存在：{shot_id}")
                return

            project = self._project_service.get_project(project_id=project_id)
            if not project:
                self.bridge_error.emit("项目不存在")
                return

            if not provider_name:
                config_mgr = self._container.config_manager()
                provider_name = config_mgr.settings.default_provider
            if not provider_name:
                self.bridge_error.emit("未配置默认视频生成供应商")
                return

            provider_cfg = self._container.config_manager().get_provider_config(
                name=provider_name, provider_type="video",
            )
            params = (provider_cfg.default_params if provider_cfg else {}).copy()
            params["resolution"] = project.resolution
            params["ratio"] = project.aspect_ratio
            if storyboard.duration > 0:
                params["duration"] = int(storyboard.duration)

            visual_style_name = None
            if project.visual_style_id:
                visual_style = self._visual_style_service.get_style(project.visual_style_id)
                if visual_style:
                    visual_style_name = visual_style.name

            characters = self._character_service.list_characters(project_id=project_id)
            workspace_root = self._container.config.workspace_root()
            reference_images_paths, reference_images_info = self._build_shot_reference_images(
                storyboard,
                characters,
                workspace_root,
                use_storyboard_design=True,
                use_character_design=True,
            )

            scenes = self._screenplay_service.list_scenes(project_id=project_id)
            shot_list = self._storyboard_service.list_storyboards(project_id=project_id)
            idx = next((j for j, s in enumerate(shot_list) if s.id == shot_id), -1)
            prev_shot = shot_list[idx - 1] if idx > 0 else None
            next_shot = shot_list[idx + 1] if idx >= 0 and idx < len(shot_list) - 1 else None
            scene_map = {s.id: s for s in scenes}
            scene = scene_map.get(storyboard.scene_id)

            request = self._build_video_request_for_shot(
                storyboard,
                project,
                provider_name=provider_name,
                params=params,
                reference_images=reference_images_paths,
                reference_images_info=reference_images_info,
                visual_style=visual_style_name,
                prev_shot=prev_shot,
                next_shot=next_shot,
                scene=scene,
            )
            video_service = self._container.video_service()
            video_service.start_shot_video(request, wait_submit=False)
        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            self.bridge_error.emit(error_msg)

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

            char_info = self._build_character_info(project_id, storyboard.content)

            shot_size_map = {
                "extreme_close_up": "特写", "close_up": "近景", "medium_shot": "中景",
                "full_shot": "全景", "long_shot": "远景", "extreme_long_shot": "大远景",
            }
            shot_size_text = shot_size_map.get(storyboard.shot_size.value, "中景")

            visual_style = ""
            project = self._project_service.get_project(project_id=project_id)
            if self._visual_style_service and project and project.visual_style_id:
                style = self._visual_style_service.get_style(project.visual_style_id)
                if style:
                    visual_style = style.name

            self._mark_design_generating(storyboard_id)
            try:
                self._image_service.start_storyboard_design_image(
                    content=storyboard.content,
                    storyboard_id=storyboard_id,
                    project_id=project_id,
                    scene_number=storyboard.scene_number,
                    shot_number=storyboard.shot_number,
                    shot_size=shot_size_text,
                    camera_movement=storyboard.camera_movement,
                    notes=storyboard.notes,
                    character_info=char_info,
                    visual_style=visual_style,
                    project_name=self._get_project_name(project_id),
                    aspect_ratio=project.aspect_ratio if project else "",
                )
            except Exception:
                self._unmark_design_generating(storyboard_id)
                raise

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

            visual_style = ""
            project = self._project_service.get_project(project_id=project_id) if self._project_service else None
            if self._visual_style_service and project and project.visual_style_id:
                style = self._visual_style_service.get_style(project.visual_style_id)
                if style:
                    visual_style = style.name

            shot_list = []
            project_name = self._get_project_name(project_id)
            aspect_ratio = project.aspect_ratio if project else ""
            for shot in shots:
                if not shot.content or not shot.content.strip():
                    continue
                shot_list.append({
                    "storyboard_id": shot.id,
                    "project_id": project_id,
                    "scene_number": shot.scene_number,
                    "shot_number": shot.shot_number,
                    "content": shot.content,
                    "shot_size": shot.shot_size,
                    "camera_movement": shot.camera_movement,
                    "notes": shot.notes,
                    "character_info": self._build_character_info(project_id, shot.content),
                    "visual_style": visual_style,
                    "project_name": project_name,
                    "aspect_ratio": aspect_ratio,
                })

            if not shot_list:
                self.bridge_error.emit("没有有效分镜可以生成设计图")
                return

            worker = self._image_service.start_batch_storyboard_design_images(
                shot_list=shot_list,
                parent=self,
            )

            def on_progress(current: int, message: str, count_info: str) -> None:
                self.batch_progress.emit(current, len(shot_list), message)

            def on_finished(success_count: int, total: int) -> None:
                self.batch_done.emit(success_count, total)
                self.load_for_project(project_id)

            def on_shot_design_started(shot_id: int) -> None:
                self._mark_design_generating(shot_id)

            def on_shot_design_done(shot_id: int, path: str) -> None:
                self._unmark_design_generating(shot_id)
                workspace_root = self._container.config.workspace_root()
                absolute_path = to_absolute_path(path, workspace_root)
                self._model.update_design_image(shot_id, absolute_path)
                if self._cur_shot_id == shot_id:
                    self._cur_design_image = absolute_path
                    self.shot_detail_changed.emit()
                self.design_image_ready.emit(str(shot_id), absolute_path)

            def on_shot_design_failed(shot_id: int) -> None:
                self._unmark_design_generating(shot_id)

            worker.progress_update.connect(on_progress)
            worker.shot_design_started.connect(on_shot_design_started)
            worker.shot_design_done.connect(on_shot_design_done)
            worker.shot_design_failed.connect(on_shot_design_failed)
            worker.finished.connect(on_finished)
            worker.failed.connect(self.design_image_failed.emit)
            worker.finished.connect(worker.deleteLater)
            self._workers.append(worker)

        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            self.bridge_error.emit(error_msg)

    @staticmethod
    def _build_shot_reference_images(
        shot,
        characters: list,
        workspace_root: str,
        use_storyboard_design: bool = True,
        use_character_design: bool = True,
    ) -> tuple[list[str], list[dict]]:
        reference_images_paths: list[str] = []
        reference_images_info: list[dict] = []

        if use_storyboard_design and shot.design_image:
            abs_path = to_absolute_path(shot.design_image, workspace_root)
            if abs_path:
                reference_images_paths.append(abs_path)
                reference_images_info.append({
                    "type": "design",
                    "description": "",
                })

        if use_character_design:
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
                            "description": "",
                        })

        return reference_images_paths, reference_images_info

    @staticmethod
    def _collect_video_generate_preview(
        selected_shots: list,
        characters: list,
        workspace_root: str,
    ) -> dict:
        storyboard_designs: list[dict] = []
        character_designs: list[dict] = []
        seen_char_uuids: set[str] = set()

        for shot in selected_shots:
            if shot.design_image:
                abs_path = to_absolute_path(shot.design_image, workspace_root)
                if abs_path:
                    storyboard_designs.append({
                        "shotId": shot.id,
                        "label": f"{shot.scene_number}场{shot.shot_number}镜",
                        "imagePath": abs_path,
                    })

            content = shot.content or ""
            for c in characters:
                if c.uuid in seen_char_uuids:
                    continue
                if c.design_image and (c.name in content or c.ref_code in content):
                    abs_path = to_absolute_path(c.design_image, workspace_root)
                    if abs_path:
                        seen_char_uuids.add(c.uuid)
                        character_designs.append({
                            "characterName": c.name,
                            "imagePath": abs_path,
                        })

        return {
            "storyboardDesigns": storyboard_designs,
            "characterDesigns": character_designs,
        }

    @Slot(int, str, result=str)
    def get_video_generate_preview(self, project_id: int, shot_ids_json: str) -> str:
        try:
            selected_ids = json.loads(shot_ids_json) if shot_ids_json else []
            if not selected_ids:
                return json.dumps({"storyboardDesigns": [], "characterDesigns": []})

            shots = self._storyboard_service.list_storyboards(project_id=project_id)
            selected_shots = [s for s in shots if s.id in selected_ids]
            characters = self._character_service.list_characters(project_id=project_id)
            workspace_root = self._container.config.workspace_root()

            preview = self._collect_video_generate_preview(
                selected_shots, characters, workspace_root,
            )
            return json.dumps(preview, ensure_ascii=False)
        except Exception:
            return json.dumps({"storyboardDesigns": [], "characterDesigns": []})

    @Slot(int, str, bool, bool, bool, str, bool, bool)
    def batch_generate_videos(
        self,
        project_id: int,
        shot_ids_json: str,
        prompt_extend: bool = True,
        use_storyboard_design: bool = True,
        use_character_design: bool = True,
        negative_prompt: str = "",
        use_prev_shot_last_frame: bool = True,
        cross_scene_prev_frame: bool = False,
    ) -> None:
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

            shot_list_for_prompt = [s for s in shots]
            shot_list = []
            for i, shot in enumerate(selected_shots):
                scene = scene_map.get(shot.scene_id)
                idx = next((j for j, s in enumerate(shot_list_for_prompt) if s.id == shot.id), -1)
                prev_shot = shot_list_for_prompt[idx - 1] if idx > 0 else None
                next_shot = shot_list_for_prompt[idx + 1] if idx < len(shot_list_for_prompt) - 1 else None

                reference_images_paths, reference_images_info = self._build_shot_reference_images(
                    shot,
                    characters,
                    workspace_root,
                    use_storyboard_design=use_storyboard_design,
                    use_character_design=use_character_design,
                )

                shot_list.append({
                    "scene_number": shot.scene_number,
                    "shot_number": shot.shot_number,
                    "storyboard": shot,
                    "scene": scene,
                    "prev_shot": prev_shot,
                    "next_shot": next_shot,
                    "reference_images_info": reference_images_info,
                    "visual_style": visual_style_name,
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
            prev_shot_frame_service = self._container.prev_shot_frame_service()

            controller = BatchGenerationController(
                shot_list=shot_list, video_service=video_service, signal_emitter=signal_emitter,
                provider_name=provider_name, project=project, provider_cfg=provider_cfg,
                prompt_extend=prompt_extend,
                negative_prompt=negative_prompt,
                use_prev_shot_last_frame=use_prev_shot_last_frame,
                cross_scene_prev_frame=cross_scene_prev_frame,
                prev_shot_frame_service=prev_shot_frame_service,
                parent=self,
            )

            def on_progress(current: int, total: int, message: str) -> None:
                self.batch_progress.emit(current, total, message)

            def on_all_done(success: int, failed: int) -> None:
                self.batch_done.emit(success, failed)
                if controller in self._workers:
                    self._workers.remove(controller)
                controller.deleteLater()

            def on_terminated(success: int, failed: int) -> None:
                self.batch_done.emit(success, failed)
                if controller in self._workers:
                    self._workers.remove(controller)
                controller.deleteLater()

            controller.progress.connect(on_progress)
            controller.all_done.connect(on_all_done)
            controller.terminated.connect(on_terminated)
            self._workers.append(controller)
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
                    "firstFramePath": v.first_frame_path or "",
                    "lastFramePath": v.last_frame_path or "",
                    "duration": v.duration,
                    "width": v.width,
                    "height": v.height,
                    "featured": getattr(v, "featured", False),
                })
            return json.dumps(result)
        except Exception:
            return "[]"

    @Slot(int, result=str)
    def get_takes_for_shot(self, shot_id: int) -> str:
        """获取分镜的所有拍摄记录，附带关联的媒体文件信息。
        无 media 的生成中 take 也会返回。
        """
        try:
            if not self._take_service:
                return "[]"
            from loguru import logger
            from storage.repositories.generate_task_repository import GenerateTaskRepository

            takes = self._take_service.list_by_storyboard(shot_id)
            task_repo = self._container.session_manager().get_repo(GenerateTaskRepository)
            result = []
            for t in takes:
                media = None
                media_file_id = (t.media_file_id or "").strip()
                if media_file_id and hasattr(self._media_service, "get_file_by_id"):
                    try:
                        media = self._media_service.get_file_by_id(media_file_id)
                    except Exception as e:
                        logger.warning(f"读取拍摄媒体失败 take_id={t.id}, media_file_id={media_file_id}: {e}")

                has_media = bool(media_file_id)
                generating = False
                failed = False
                if not has_media and t.generate_task_id:
                    try:
                        task_info = task_repo.get_task_info(t.generate_task_id)
                        if task_info is None:
                            generating = True
                        else:
                            completed, status = task_info
                            if not completed:
                                generating = True
                            elif status == "failed":
                                failed = True
                    except Exception as e:
                        logger.warning(
                            f"读取拍摄任务状态失败 take_id={t.id}, generate_task_id={t.generate_task_id}: {e}"
                        )
                        generating = True

                video_child_task_id = 0
                if media is not None and getattr(media, "generate_task_id", 0):
                    video_child_task_id = int(media.generate_task_id)
                elif t.generate_task_id:
                    try:
                        children = task_repo.list_child_tasks_by_parent_id(t.generate_task_id)
                        for child in reversed(children):
                            child_type = (child.get("type") or "").strip().lower()
                            parent_ids = (child.get("parent_ids") or "").strip()
                            if child_type == "video" and parent_ids:
                                video_child_task_id = int(child.get("id") or 0)
                                break
                    except Exception as e:
                        logger.warning(
                            f"解析视频子任务失败 take_id={t.id}, generate_task_id={t.generate_task_id}: {e}"
                        )

                result.append({
                    "id": t.id,
                    "storyboardId": t.storyboard_id,
                    "number": t.number,
                    "mediaFileId": media_file_id,
                    "generateTaskId": t.generate_task_id or 0,
                    "videoChildTaskId": video_child_task_id,
                    "status": t.status.value if hasattr(t.status, "value") else str(t.status),
                    "comment": t.comment or "",
                    "createdAt": t.created_at,
                    "hasMedia": 1 if has_media else 0,
                    "generating": 1 if generating else 0,
                    "failed": 1 if failed else 0,
                    "filePath": media.local_path if media else "",
                    "thumbnailPath": (media.thumbnail_path or "") if media else "",
                    "firstFramePath": (media.first_frame_path or "") if media else "",
                    "lastFramePath": (media.last_frame_path or "") if media else "",
                    "duration": media.duration if media else 0,
                    "width": media.width if media else 0,
                    "height": media.height if media else 0,
                })
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            from loguru import logger
            logger.warning(f"获取拍摄记录失败 shot_id={shot_id}: {e}")
            return "[]"

    @Slot(int, str)
    def update_take_status(self, take_id: int, status: str) -> None:
        """更新拍摄记录状态"""
        try:
            if not self._take_service:
                return
            from models.enums import TakeStatus
            take_status = TakeStatus(status)
            self._take_service.update_status(take_id, take_status)
            self.takes_changed.emit()
        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            self.bridge_error.emit(error_msg)

    @Slot(int)
    def delete_take(self, take_id: int) -> None:
        """删除拍摄记录"""
        try:
            if not self._take_service:
                return
            self._take_service.delete_take(take_id)
            self.takes_changed.emit()
        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            self.bridge_error.emit(error_msg)

    def _on_design_done(self, shot_id: int, path: str) -> None:
        # Worker 内部已经保存到数据库，这里只需更新 Model 和发出信号
        self._unmark_design_generating(shot_id)
        workspace_root = self._container.config.workspace_root()
        absolute_path = to_absolute_path(path, workspace_root)
        self._model.update_design_image(shot_id, absolute_path)
        if self._cur_shot_id == shot_id:
            self._cur_design_image = absolute_path
            self.shot_detail_changed.emit()
        self.design_image_ready.emit(str(shot_id), absolute_path)

    def _on_design_failed(self, shot_id: int, error: str) -> None:
        self._unmark_design_generating(shot_id)
        self.design_image_failed.emit(error)

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
        combined_requirement = f"用户要求：{user_input}\n\n大纲参考：{outline_content}"

        self._begin_generation(project_id=project_id, scenes=scenes, clear_existing=False)

        self._generate_worker = StoryboardGenerateWorker(
            text_service=self._text_model_service, script_content=script_content, art_style=combined_requirement,
            project_id=project_id,
            project_name=self._get_project_name(project_id),
        )
        self._connect_storyboard_worker(self._generate_worker, project_id, is_optimize=False)

    def _optimize_storyboard(self, outline_content: str, scenes: list, characters: list, storyboards: list, user_input: str, project_id: int) -> None:
        script_content = self._format_script_as_text(scenes)
        character_content = self._format_characters_as_text(characters)
        current_storyboard = self._format_storyboards_as_text(storyboards)

        self._begin_generation(project_id=project_id, scenes=scenes, clear_existing=True)

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
        self._connect_storyboard_worker(self._optimize_worker, project_id, is_optimize=True)

    def _begin_generation(self, project_id: int, scenes: list, clear_existing: bool) -> None:
        self._project_id = project_id
        self._scene_map = {s.scene_number: s.id for s in scenes}
        self._generation_snapshot = list(
            self._storyboard_service.list_storyboards(project_id=project_id)
        )
        self._created_ids = []

        if clear_existing:
            for shot in self._generation_snapshot:
                self._storyboard_service.delete_storyboard(storyboard_id=shot.id)
            self._model.reset([])

        self._generation_aborted = False
        self._optimizing = True
        self.isOptimizingChanged.emit()
        self.generation_started.emit()

    def _build_storyboard_from_data(self, shot_data: dict):
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

        scene_number = shot_data.get("scene_number", 1)
        scene_id = self._scene_map.get(scene_number, 0)
        shot_size_value = shot_data.get("shot_size", "medium_shot")
        if isinstance(shot_size_value, str):
            shot_size = shot_size_map.get(shot_size_value, ShotSize.MEDIUM_SHOT)
        else:
            shot_size = ShotSize(shot_size_value)

        return self._storyboard_service.create_storyboard(
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
            notes=shot_data.get("notes", ""),
        )

    def _on_shot_item_ready(self, data: dict) -> None:
        if self._generation_aborted:
            return
        try:
            storyboard = self._build_storyboard_from_data(data)
            self._created_ids.append(storyboard.id)
            self._model.append(storyboard)
            self.shot_added.emit()
        except Exception as e:
            self._generation_aborted = True
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            self._rollback_generation()
            self._optimizing = False
            self.isOptimizingChanged.emit()
            self.storyboard_generation_failed.emit(f"保存失败：{error_msg}")

    def _rollback_generation(self) -> None:
        for shot_id in self._created_ids:
            try:
                self._storyboard_service.delete_storyboard(storyboard_id=shot_id)
            except Exception:
                pass
        self._created_ids = []

        for shot in self._generation_snapshot:
            self._storyboard_service.create_storyboard(
                scene_id=shot.scene_id,
                scene_number=shot.scene_number,
                shot_number=shot.shot_number,
                shot_size=shot.shot_size,
                camera_movement=shot.camera_movement,
                content=shot.content,
                sound_effect=shot.sound_effect,
                ambient_sound=shot.ambient_sound,
                background_music=shot.background_music,
                duration=shot.duration,
                notes=shot.notes,
                design_image=shot.design_image,
                seed=shot.seed,
            )
        if self._project_id >= 0:
            self.load_for_project(self._project_id)

    def _finish_generation(self) -> None:
        self._generation_snapshot = []
        self._created_ids = []
        self._optimizing = False
        self.isOptimizingChanged.emit()

    def _connect_storyboard_worker(self, worker, project_id: int, is_optimize: bool) -> None:
        def on_item_ready(data: dict) -> None:
            self._on_shot_item_ready(data)

        def on_finished(result: list) -> None:
            if self._generation_aborted:
                return
            try:
                if not result:
                    self._generation_aborted = True
                    self._rollback_generation()
                    self._optimizing = False
                    self.isOptimizingChanged.emit()
                    self.storyboard_generation_failed.emit("AI 返回的分镜数据为空")
                    return
                self._finish_generation()
                if is_optimize:
                    self.storyboard_optimized.emit(len(result))
                else:
                    self.storyboard_generated.emit(len(result))
            except Exception as e:
                self.storyboard_generation_failed.emit(f"保存失败：{e}")

        def on_failed(err: str) -> None:
            if self._generation_aborted:
                return
            self._generation_aborted = True
            self._rollback_generation()
            self._optimizing = False
            self.isOptimizingChanged.emit()
            prefix = "优化分镜失败：" if is_optimize else "生成分镜失败："
            self.storyboard_generation_failed.emit(f"{prefix}{err}")

        worker.item_ready.connect(on_item_ready)
        worker.finished.connect(on_finished)
        worker.failed.connect(on_failed)
        worker.finished.connect(worker.deleteLater)
        worker.start()

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
