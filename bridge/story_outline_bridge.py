from __future__ import annotations

from loguru import logger

from PySide6.QtCore import QObject, Property, Signal, Slot

from bridge.models.history_model import HistoryListModel
from bridge.workers import OptimizeWorker


class StoryOutlineBridge(QObject):
    loaded = Signal(str)
    saved = Signal()
    optimize_finished = Signal(str)
    optimize_failed = Signal(str)
    isOptimizingChanged = Signal()
    error = Signal(str)

    def __init__(self, story_outline_service, text_model_service, parent=None):
        super().__init__(parent)
        self._service = story_outline_service
        self._text_service = text_model_service
        self._history_model = HistoryListModel(self)
        self._outline_id: int = -1
        self._project_id: int = -1
        self._content: str = ""
        self._loading: bool = False
        self._optimizing: bool = False
        self._worker: OptimizeWorker | None = None

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
            outline = self._service.get_or_create_story_outline(project_id)
            self._outline_id = outline.id
            self._content = outline.content
            self.loaded.emit(self._content)
            logger.info(f"加载故事大纲：project={project_id}, id={outline.id}")
        except Exception as e:
            logger.exception("加载故事大纲失败")
            self.error.emit(str(e))
        finally:
            self._loading = False

    @Slot(str)
    def save(self, content: str) -> None:
        if self._outline_id < 0:
            self.error.emit("大纲未加载")
            return
        try:
            self._service.update_story_outline(self._outline_id, content)
            self._content = content
            self.saved.emit()
            logger.info(f"保存故事大纲：{self._outline_id}")
        except Exception as e:
            logger.exception("保存故事大纲失败")
            self.error.emit(str(e))

    @Slot(int, result=str)
    def get_outline_content(self, project_id: int) -> str:
        try:
            outline = self._service.get_or_create_story_outline(project_id)
            return outline.content if outline else ""
        except Exception as e:
            logger.exception(f"获取大纲内容失败: {e}")
            return ""

    @Slot()
    def load_history(self) -> None:
        if self._outline_id < 0:
            return
        try:
            history_list = self._service.list_history(self._outline_id)
            self._history_model.reset(history_list)
        except Exception as e:
            logger.exception("加载历史版本失败")
            self.error.emit(str(e))

    @Slot(int)
    def restore_history(self, history_id: int) -> None:
        if self._outline_id < 0:
            return
        try:
            self._service.restore_from_history(self._outline_id, history_id)
            # 重新加载
            if self._project_id >= 0:
                self.load(self._project_id)
        except Exception as e:
            logger.exception("恢复历史版本失败")
            self.error.emit(str(e))

    @Slot(str, str)
    def optimize(self, requirement: str, current_content: str) -> None:
        if self._optimizing:
            return

        self._content = current_content

        messages = [
            {
                "role": "system",
                "content": "你是一个专业的视频项目策划助手。请根据用户的要求优化视频项目大纲。保持大纲的整体结构和核心内容，直接输出优化后的大纲内容，不要添加任何解释或说明。",
            },
            {
                "role": "user",
                "content": f"原始大纲：\n{current_content if current_content.strip() else '（空大纲）'}\n\n优化要求：{requirement}\n\n请根据要求优化这份大纲，直接输出优化后的大纲内容。",
            },
        ]

        self._optimizing = True
        self.isOptimizingChanged.emit()
        self._worker = OptimizeWorker(self._text_service, messages)

        def on_finished(result: str) -> None:
            self._optimizing = False
            self.isOptimizingChanged.emit()
            self.optimize_finished.emit(result)

        def on_failed(err: str) -> None:
            self._optimizing = False
            self.isOptimizingChanged.emit()
            self.optimize_failed.emit(err)

        self._worker.finished.connect(on_finished)
        self._worker.failed.connect(on_failed)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.start()
