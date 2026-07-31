from __future__ import annotations

from loguru import logger

from PySide6.QtCore import QObject, Property, Signal, Slot

from bridge.models.scene_model import SceneListModel
from bridge.models.screenplay_history_model import ScreenplayHistoryListModel
from bridge.workers import ScriptGenerateWorker
from models.enums import SceneLocation, SceneTime


class ScreenplayBridge(QObject):
    scenes_loaded = Signal()
    scene_saved = Signal()
    scene_deleted = Signal()
    history_saved = Signal()
    history_restored = Signal()
    script_generated = Signal(str, int)  # title, scene_count
    script_failed = Signal(str)
    error = Signal(str)
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

    def __init__(self, screenplay_service, text_model_service, parent=None):
        super().__init__(parent)
        self._service = screenplay_service
        self._text_service = text_model_service
        self._scene_model = SceneListModel(self)
        self._history_model = ScreenplayHistoryListModel(self)
        self._project_id: int = -1
        self._worker: ScriptGenerateWorker | None = None
        self._cur_scene_id: int = -1
        self._cur_scene_number: int = 0
        self._cur_location_type_index: int = 0
        self._cur_location: str = ""
        self._cur_time_type_index: int = 0
        self._cur_time_detail: str = ""
        self._cur_content: str = ""

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

    @Slot(int)
    def load_for_project(self, project_id: int) -> None:
        self._project_id = project_id
        self._load_scenes()
        self._load_history()

    def _load_scenes(self) -> None:
        if self._project_id < 0:
            return
        try:
            scenes = self._service.list_scenes(self._project_id)
            self._scene_model.reset(scenes)
            self.scenes_loaded.emit()
        except Exception as e:
            logger.exception("加载场次列表失败")
            self.error.emit(str(e))

    def _load_history(self) -> None:
        if self._project_id < 0:
            return
        try:
            timestamps = self._service.list_history_timestamps(self._project_id)
            items = []
            for ts in timestamps:
                scenes = self._service.list_history_by_timestamp(self._project_id, ts)
                items.append((ts, len(scenes)))
            self._history_model.reset(items)
        except Exception as e:
            logger.exception("加载历史版本失败")
            self.error.emit(str(e))

    @Slot(int)
    def load_scene(self, scene_id: int) -> None:
        try:
            scene = self._service.get_scene(scene_id)
            if not scene:
                self.error.emit("场次不存在")
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
            logger.exception("加载场次失败")
            self.error.emit(str(e))

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
            self.error.emit("请输入地点")
            return
        if not content.strip():
            self.error.emit("请输入场次内容")
            return

        location_type = self._LOCATION_TYPE_MAP.get(location_type_index, SceneLocation.INTERIOR)
        time_type = self._TIME_TYPE_MAP.get(time_type_index, SceneTime.DAY)

        try:
            self._service.update_scene(
                scene_id,
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
            logger.exception("保存场次失败")
            self.error.emit(str(e))

    @Slot(int)
    def delete_scene(self, scene_id: int) -> None:
        try:
            self._service.delete_scene(scene_id)
            self.scene_deleted.emit()
            self._load_scenes()
        except Exception as e:
            logger.exception("删除场次失败")
            self.error.emit(str(e))

    @Slot()
    def save_history(self) -> None:
        if self._project_id < 0:
            return
        try:
            self._service.save_history(self._project_id)
            self._load_history()
            self.history_saved.emit()
        except Exception as e:
            logger.exception("保存历史版本失败")
            self.error.emit(str(e))

    @Slot(int)
    def restore_history(self, created_at: int) -> None:
        if self._project_id < 0:
            return
        try:
            self._service.restore_from_history(self._project_id, created_at)
            self._load_scenes()
            self._load_history()
            self.history_restored.emit()
        except Exception as e:
            logger.exception("恢复历史版本失败")
            self.error.emit(str(e))

    @Slot(str)
    def generate_script(self, outline_content: str) -> None:
        if not outline_content.strip():
            self.error.emit("大纲内容为空，无法生成剧本")
            return

        self._worker = ScriptGenerateWorker(self._text_service, outline_content)

        def on_finished(title: str, scenes: list) -> None:
            try:
                if self._project_id >= 0 and scenes:
                    self._service.batch_create_scenes(self._project_id, scenes)
                self._load_scenes()
                self._load_history()
                self.script_generated.emit(title, len(scenes))
            except Exception as e:
                logger.exception("保存生成的剧本失败")
                self.script_failed.emit(str(e))

        def on_failed(err: str) -> None:
            self.script_failed.emit(err)

        self._worker.finished.connect(on_finished)
        self._worker.failed.connect(on_failed)
        self._worker.start()
