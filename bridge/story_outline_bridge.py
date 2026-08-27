from __future__ import annotations

from PySide6.QtCore import QObject, Property, Signal, Slot

from bridge.models.history_model import HistoryListModel
from bridge.workers import OutlineOptimizeWorker


class StoryOutlineBridge(QObject):
    loaded = Signal(str)
    saved = Signal()
    optimize_started = Signal()
    optimize_chunk = Signal(str)
    optimize_finished = Signal(str)
    optimize_failed = Signal(str)
    isOptimizingChanged = Signal()
    bridge_error = Signal(str)

    def __init__(self, story_outline_service, text_model_service, project_service=None, parent=None):
        super().__init__(parent)
        self._service = story_outline_service
        self._text_service = text_model_service
        self._project_service = project_service
        self._history_model = HistoryListModel(self)
        self._outline_id: int = -1
        self._project_id: int = -1
        self._content: str = ""
        self._loading: bool = False
        self._optimizing: bool = False
        self._worker: OutlineOptimizeWorker | None = None

    def _get_project_name(self) -> str | None:
        if self._project_service and self._project_id >= 0:
            project = self._project_service.get_project(project_id=self._project_id)
            return project.name if project else None
        return None

    @Property(QObject, constant=True)
    def historyModel(self):
        return self._history_model

    @Property(str, notify=loaded)
    def content(self):
        return self._content

    @Property(bool, constant=False)
    def isLoading(self):
        return self._loading

    @Property(bool, notify=isOptimizingChanged)
    def isOptimizing(self):
        return self._optimizing

    @Slot(int)
    def load(self, project_id: int) -> None:
        self._project_id = project_id
        self._loading = True
        try:
            outline = self._service.get_or_create_story_outline(project_id=project_id)
            self._outline_id = outline.id
            self._content = outline.content
            self.loaded.emit(self._content)
        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            self.bridge_error.emit(error_msg)
        finally:
            self._loading = False

    @Slot(str)
    def save(self, content: str) -> None:
        if self._outline_id < 0:
            self.bridge_error.emit("大纲未加载")
            return
        try:
            self._service.update_story_outline(story_outline_id=self._outline_id, content=content)
            self._content = content
            self.saved.emit()
        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            self.bridge_error.emit(error_msg)

    @Slot(int, result=str)
    def get_outline_content(self, project_id: int) -> str:
        try:
            outline = self._service.get_or_create_story_outline(project_id=project_id)
            return outline.content if outline else ""
        except Exception:
            return ""

    @Slot()
    def load_history(self) -> None:
        if self._outline_id < 0:
            return
        try:
            history_list = self._service.list_history(story_outline_id=self._outline_id)
            self._history_model.reset(history_list)
        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            self.bridge_error.emit(error_msg)

    @Slot(int)
    def restore_history(self, history_id: int) -> None:
        if self._outline_id < 0:
            return
        try:
            self._service.restore_from_history(story_outline_id=self._outline_id, history_id=history_id)
            # 重新加载
            if self._project_id >= 0:
                self.load(self._project_id)
        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            self.bridge_error.emit(error_msg)

    @Slot(str, str)
    def optimize(self, requirement: str, current_content: str) -> None:
        if self._optimizing:
            return

        self._content = current_content

        self._optimizing = True
        self.isOptimizingChanged.emit()
        self._worker = OutlineOptimizeWorker(
            text_service=self._text_service,
            original_content=current_content,
            user_requirement=requirement,
            project_id=self._project_id if self._project_id >= 0 else None,
            project_name=self._get_project_name(),
        )

        def on_started() -> None:
            self.optimize_started.emit()

        def on_chunk(delta: str) -> None:
            self.optimize_chunk.emit(delta)

        def on_finished(result: str) -> None:
            self._optimizing = False
            self.isOptimizingChanged.emit()
            self.optimize_finished.emit(result)

        def on_failed(err: str) -> None:
            self._optimizing = False
            self.isOptimizingChanged.emit()
            self.optimize_failed.emit(err)

        self._worker.started.connect(on_started)
        self._worker.chunk.connect(on_chunk)
        self._worker.finished.connect(on_finished)
        self._worker.failed.connect(on_failed)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.start()
