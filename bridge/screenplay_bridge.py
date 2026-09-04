from __future__ import annotations

from PySide6.QtCore import QObject, Property, Signal, Slot

from bridge.models.scene_model import SceneListModel
from bridge.models.screenplay_history_model import ScreenplayHistoryListModel
from bridge.workers import ScriptGenerateWorker, ScreenplayOptimizeWorker
from models.enums import SceneLocation, SceneTime


class ScreenplayBridge(QObject):
    scenes_loaded = Signal()
    scene_saved = Signal()
    scene_deleted = Signal()
    new_scene_created = Signal()
    history_saved = Signal()
    history_restored = Signal()
    script_generated = Signal(str, int)  # title, scene_count
    script_failed = Signal(str)
    script_optimized = Signal(int)  # scene_count
    isOptimizingChanged = Signal()
    generation_started = Signal()
    scene_added = Signal()
    bridge_error = Signal(str)
    current_scene_changed = Signal()

    _LOCATION_TYPE_MAP = {
        0: SceneLocation.INTERIOR,
        1: SceneLocation.EXTERIOR,
        2: SceneLocation.INTERIOR_EXTERIOR,
    }
    _LOCATION_TYPE_REVERSE = {v: k for k, v in _LOCATION_TYPE_MAP.items()}

    _TIME_TYPE_MAP = {
        0: SceneTime.DAY,
        1: SceneTime.NIGHT,
        2: SceneTime.DAWN,
        3: SceneTime.DUSK,
        4: SceneTime.EVENING,
        5: SceneTime.CUSTOM,
    }
    _TIME_TYPE_REVERSE = {v: k for k, v in _TIME_TYPE_MAP.items()}

    def __init__(self, screenplay_service, text_model_service, story_outline_service,
                 project_service=None, parent=None):
        super().__init__(parent)
        self._service = screenplay_service
        self._text_service = text_model_service
        self._story_outline_service = story_outline_service
        self._project_service = project_service
        self._scene_model = SceneListModel(self)
        self._history_model = ScreenplayHistoryListModel(self)
        self._project_id: int = -1
        self._worker: ScriptGenerateWorker | None = None
        self._optimize_worker: ScreenplayOptimizeWorker | None = None
        self._optimizing: bool = False
        self._generation_snapshot: list = []
        self._created_ids: list[int] = []
        self._generation_aborted: bool = False
        self._cur_scene_id: int = -1
        self._cur_scene_number: int = 0
        self._cur_location_type_index: int = 0
        self._cur_location: str = ""
        self._cur_time_type_index: int = 0
        self._cur_time_detail: str = ""
        self._cur_content: str = ""

    def _get_project_name(self) -> str | None:
        if self._project_service and self._project_id >= 0:
            project = self._project_service.get_project(project_id=self._project_id)
            return project.name if project else None
        return None

    @Property(QObject, constant=True)
    def sceneModel(self):
        return self._scene_model

    @Property(QObject, constant=True)
    def historyModel(self):
        return self._history_model

    @Property(int, notify=current_scene_changed)
    def curSceneId(self):
        return self._cur_scene_id

    @Property(int, notify=current_scene_changed)
    def curSceneNumber(self):
        return self._cur_scene_number

    @Property(int, notify=current_scene_changed)
    def curLocationTypeIndex(self):
        return self._cur_location_type_index

    @Property(str, notify=current_scene_changed)
    def curLocation(self):
        return self._cur_location

    @Property(int, notify=current_scene_changed)
    def curTimeTypeIndex(self):
        return self._cur_time_type_index

    @Property(str, notify=current_scene_changed)
    def curTimeDetail(self):
        return self._cur_time_detail

    @Property(str, notify=current_scene_changed)
    def curContent(self):
        return self._cur_content

    @Property(bool, notify=isOptimizingChanged)
    def isOptimizing(self):
        return self._optimizing

    @Slot(int)
    def load_for_project(self, project_id: int) -> None:
        self._project_id = project_id
        self._load_scenes()
        self._load_history()

    def _load_scenes(self) -> None:
        if self._project_id < 0:
            return
        try:
            scenes = self._service.list_scenes(project_id=self._project_id)
            self._scene_model.reset(scenes)
            self.scenes_loaded.emit()
        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            self.bridge_error.emit(error_msg)

    def _load_history(self) -> None:
        if self._project_id < 0:
            return
        try:
            timestamps = self._service.list_history_timestamps(project_id=self._project_id)
            items = []
            for ts in timestamps:
                scenes = self._service.list_history_by_timestamp(project_id=self._project_id, created_at=ts)
                items.append((ts, len(scenes)))
            self._history_model.reset(items)
        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            self.bridge_error.emit(error_msg)

    @Slot(int)
    def load_scene(self, scene_id: int) -> None:
        try:
            scene = self._service.get_scene(scene_id=scene_id)
            if not scene:
                self.bridge_error.emit("场次不存在")
                return

            self._cur_scene_id = scene.id
            self._cur_scene_number = scene.scene_number
            self._cur_location_type_index = self._LOCATION_TYPE_REVERSE.get(scene.location_type, 0)
            self._cur_location = scene.location
            self._cur_time_type_index = self._TIME_TYPE_REVERSE.get(scene.time_type, 0)
            self._cur_time_detail = scene.time_detail
            self._cur_content = scene.content
            self.current_scene_changed.emit()
        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            self.bridge_error.emit(error_msg)

    @Slot(int, int, str, int, str, str)
    def save_scene(
        self,
        scene_id: int,
        location_type_index: int,
        location: str,
        time_type_index: int,
        time_detail: str,
        content: str,
    ) -> None:
        if not location.strip():
            self.bridge_error.emit("请输入地点")
            return
        if not content.strip():
            self.bridge_error.emit("请输入场次内容")
            return

        location_type = self._LOCATION_TYPE_MAP.get(location_type_index, SceneLocation.INTERIOR)
        time_type = self._TIME_TYPE_MAP.get(time_type_index, SceneTime.DAY)

        try:
            self._service.update_scene(
                scene_id=scene_id,
                location_type=location_type,
                location=location.strip(),
                time_type=time_type,
                time_detail=time_detail.strip(),
                content=content.strip(),
            )
            self._cur_content = content.strip()
            self.scene_saved.emit()
            self._load_scenes()
        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            self.bridge_error.emit(error_msg)

    @Slot(int)
    def delete_scene(self, scene_id: int) -> None:
        try:
            self._service.delete_scene(scene_id=scene_id)
            self.scene_deleted.emit()
            self._load_scenes()
        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            self.bridge_error.emit(error_msg)

    @Slot(int)
    def prepare_new_scene(self, project_id: int) -> None:
        try:
            scenes = self._service.list_scenes(project_id=project_id)
            max_num = max((s.scene_number for s in scenes), default=0)
            self._cur_scene_id = -1
            self._cur_scene_number = max_num + 1
            self._cur_location_type_index = 0
            self._cur_location = ""
            self._cur_time_type_index = 0
            self._cur_time_detail = ""
            self._cur_content = ""
            self.current_scene_changed.emit()
            self.new_scene_created.emit()
        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            self.bridge_error.emit(error_msg)

    @Slot(int, int, str, int, str, str)
    def create_scene(
        self,
        project_id: int,
        location_type_index: int,
        location: str,
        time_type_index: int,
        time_detail: str,
        content: str,
    ) -> None:
        if not location.strip():
            self.bridge_error.emit("请输入地点")
            return
        if not content.strip():
            self.bridge_error.emit("请输入场次内容")
            return

        location_type = self._LOCATION_TYPE_MAP.get(location_type_index, SceneLocation.INTERIOR)
        time_type = self._TIME_TYPE_MAP.get(time_type_index, SceneTime.DAY)

        try:
            new_scene = self._service.create_scene(
                project_id=project_id,
                scene_number=self._cur_scene_number,
                location_type=location_type,
                location=location.strip(),
                time_type=time_type,
                time_detail=time_detail.strip(),
                content=content.strip(),
            )
            self._load_scenes()
            self.load_scene(new_scene.id)
            self.scene_saved.emit()
        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            self.bridge_error.emit(error_msg)

    @Slot()
    def save_history(self) -> None:
        if self._project_id < 0:
            return
        try:
            self._service.save_history(project_id=self._project_id)
            self._load_history()
            self.history_saved.emit()
        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            self.bridge_error.emit(error_msg)

    @Slot(int)
    def restore_history(self, created_at: int) -> None:
        if self._project_id < 0:
            return
        try:
            self._service.restore_from_history(project_id=self._project_id, created_at=created_at)
            self._load_scenes()
            self._load_history()
            self.history_restored.emit()
        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            self.bridge_error.emit(error_msg)

    @Slot(str)
    def generate_script(self, outline_content: str) -> None:
        if not outline_content.strip():
            self.bridge_error.emit("大纲内容为空，无法生成剧本")
            return

        self._begin_generation(clear_existing=False)

        self._worker = ScriptGenerateWorker(
            text_service=self._text_service, outline_content=outline_content,
            project_id=self._project_id if self._project_id >= 0 else None,
            project_name=self._get_project_name(),
        )
        self._connect_script_worker(self._worker, is_optimize=False)

    def _begin_generation(self, clear_existing: bool) -> None:
        if self._project_id >= 0:
            self._generation_snapshot = list(self._service.list_scenes(project_id=self._project_id))
        else:
            self._generation_snapshot = []
        self._created_ids = []

        if clear_existing and self._project_id >= 0:
            for scene in self._generation_snapshot:
                self._service.delete_scene(scene_id=scene.id)
            self._scene_model.reset([])

        self._generation_aborted = False
        self._optimizing = True
        self.isOptimizingChanged.emit()
        self.generation_started.emit()

    def _create_scene_from_data(self, data: dict):
        location_type = data["location_type"]
        if isinstance(location_type, str):
            location_type = SceneLocation(location_type)

        time_type = data["time_type"]
        if isinstance(time_type, str):
            time_type = SceneTime(time_type)

        return self._service.create_scene(
            project_id=self._project_id,
            scene_number=data["scene_number"],
            location_type=location_type,
            location=data["location"],
            time_type=time_type,
            time_detail=data.get("time_detail", ""),
            content=data["content"],
        )

    def _on_scene_item_ready(self, data: dict) -> None:
        if self._generation_aborted or self._project_id < 0:
            return
        try:
            scene = self._create_scene_from_data(data)
            self._created_ids.append(scene.id)
            self._scene_model.append(scene)
            self.scene_added.emit()
        except Exception as e:
            self._generation_aborted = True
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            self._rollback_generation()
            self._optimizing = False
            self.isOptimizingChanged.emit()
            self.script_failed.emit(f"保存失败：{error_msg}")

    def _rollback_generation(self) -> None:
        for scene_id in self._created_ids:
            try:
                self._service.delete_scene(scene_id=scene_id)
            except Exception:
                pass
        self._created_ids = []

        if self._project_id >= 0:
            for scene in self._generation_snapshot:
                self._service.create_scene(
                    project_id=self._project_id,
                    scene_number=scene.scene_number,
                    location_type=scene.location_type,
                    location=scene.location,
                    time_type=scene.time_type,
                    time_detail=scene.time_detail,
                    content=scene.content,
                )
        self._load_scenes()

    def _finish_generation(self) -> None:
        self._generation_snapshot = []
        self._created_ids = []
        self._optimizing = False
        self.isOptimizingChanged.emit()
        self._load_history()

    def _connect_script_worker(self, worker, is_optimize: bool) -> None:
        def on_started() -> None:
            pass

        def on_item_ready(data: dict) -> None:
            self._on_scene_item_ready(data)

        def on_finished(title: str, scenes: list) -> None:
            if self._generation_aborted:
                return
            try:
                if not scenes:
                    self._generation_aborted = True
                    self._rollback_generation()
                    self._optimizing = False
                    self.isOptimizingChanged.emit()
                    self.script_failed.emit("AI 返回的剧本数据为空")
                    return
                self._finish_generation()
                if is_optimize:
                    self.script_optimized.emit(len(scenes))
                else:
                    self.script_generated.emit(title, len(scenes))
            except Exception as e:
                error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
                self.script_failed.emit(error_msg)

        def on_failed(err: str) -> None:
            if self._generation_aborted:
                return
            self._generation_aborted = True
            self._rollback_generation()
            self._optimizing = False
            self.isOptimizingChanged.emit()
            self.script_failed.emit(err)

        worker.started.connect(on_started)
        worker.item_ready.connect(on_item_ready)
        worker.finished.connect(on_finished)
        worker.failed.connect(on_failed)
        worker.finished.connect(worker.deleteLater)
        worker.start()

    @Slot(str, int)
    def optimize_with_ai(self, user_input: str, project_id: int) -> None:
        if self._optimizing:
            return

        try:
            outline = self._story_outline_service.get_or_create_story_outline(project_id=project_id)
            if not outline.content.strip():
                self.bridge_error.emit("大纲内容为空，无法生成剧本")
                return

            scenes = self._service.list_scenes(project_id=project_id)

            if not scenes:
                self._generate_from_outline(outline.content, user_input)
            else:
                self._optimize_existing_script(outline.content, scenes, user_input)

        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            self.bridge_error.emit(error_msg)

    def _generate_from_outline(self, outline_content: str, user_input: str) -> None:
        combined_content = f"{outline_content}\n\n用户要求：{user_input}"
        self.generate_script(combined_content)

    def _optimize_existing_script(self, outline_content: str, scenes: list, user_input: str) -> None:
        current_script = self._format_scenes_as_text(scenes)
        self._begin_generation(clear_existing=True)

        self._optimize_worker = ScreenplayOptimizeWorker(
            text_service=self._text_service,
            outline_content=outline_content,
            current_script=current_script,
            user_requirement=user_input,
            project_id=self._project_id if self._project_id >= 0 else None,
            project_name=self._get_project_name(),
        )
        self._connect_script_worker(self._optimize_worker, is_optimize=True)

    def _format_scenes_as_text(self, scenes: list) -> str:
        lines = []
        for scene in scenes:
            # 场次标题
            location_type_str = {
                SceneLocation.INTERIOR: "内景",
                SceneLocation.EXTERIOR: "外景",
                SceneLocation.INTERIOR_EXTERIOR: "内景/外景",
            }.get(scene.location_type, "内景")

            time_type_str = {
                SceneTime.DAY: "日",
                SceneTime.NIGHT: "夜",
                SceneTime.DAWN: "晨",
                SceneTime.DUSK: "黄昏",
                SceneTime.EVENING: "傍晚",
                SceneTime.CUSTOM: scene.time_detail,
            }.get(scene.time_type, "日")

            lines.append(f"第{scene.scene_number}场 {location_type_str} {scene.location} {time_type_str}")
            lines.append("")
            lines.append(scene.content)
            lines.append("")
            lines.append("")

        return "\n".join(lines)
