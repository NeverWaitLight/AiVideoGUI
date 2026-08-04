from __future__ import annotations

from loguru import logger

from PySide6.QtCore import QObject, Property, Signal, Slot

from bridge.models.media_file_model import MediaFileListModel
from bridge.workers import VideoExportWorker


class MediaBridge(QObject):
    files_changed = Signal()
    export_progress = Signal(int, str)
    export_finished = Signal(str)
    export_failed = Signal(str)

    def __init__(self, media_service, parent=None):
        super().__init__(parent)
        self._media_service = media_service
        self._model = MediaFileListModel(self)
        self._export_worker = None

    @Property(QObject, constant=True)
    def model(self):
        return self._model

    @Slot()
    def load_files(self) -> None:
        files = self._media_service.list_files()
        self._model.reset(files)

    @Slot(str)
    def load_files_by_type(self, media_type: str = "") -> None:
        files = self._media_service.list_files(media_type=media_type or None)
        self._model.reset(files)

    @Slot(str, str)
    def load_files_search(self, media_type: str, search: str) -> None:
        files = self._media_service.list_files(
            media_type=media_type or None, keyword=search or None,
        )
        self._model.reset(files)

    @Slot(int)
    def load_project_files(self, project_id: int) -> None:
        files = self._media_service.list_files(project_id=project_id)
        self._model.reset(files)

    @Slot(str, str, int)
    def load_files_filtered(self, media_type: str, keyword: str, project_id: int) -> None:
        files = self._media_service.list_files(
            media_type=media_type or None,
            keyword=keyword or None,
            project_id=project_id if project_id > 0 else None,
        )
        self._model.reset(files)

    @Slot(list)
    def import_files(self, file_paths: list) -> None:
        self._media_service.import_files(file_paths)
        self.load_files()
        self.files_changed.emit()

    @Slot(str)
    def delete_file(self, file_id: str) -> None:
        self._media_service.delete_file(file_id)
        self._model.remove_by_id(file_id)
        self.files_changed.emit()

    @Slot(str, int)
    def set_featured(self, file_id: str, storyboard_id: int) -> None:
        self._media_service.set_featured(file_id, storyboard_id)

    @Slot(int, str)
    def export_project_video(self, project_id: int, output_path: str) -> None:
        if self._export_worker and self._export_worker.isRunning():
            logger.warning("已有导出任务正在进行")
            return

        self._export_worker = VideoExportWorker(self._media_service, project_id, output_path, self)
        self._export_worker.progress.connect(self._on_export_progress)
        self._export_worker.finished.connect(self._on_export_finished)
        self._export_worker.failed.connect(self._on_export_failed)
        self._export_worker.start()
        logger.info(f"开始导出项目视频: project_id={project_id}, output_path={output_path}")

    def _on_export_progress(self, percent: int, message: str) -> None:
        self.export_progress.emit(percent, message)

    def _on_export_finished(self, output_path: str) -> None:
        self.export_finished.emit(output_path)
        logger.info(f"视频导出完成: {output_path}")
        if self._export_worker:
            self._export_worker.deleteLater()
            self._export_worker = None

    def _on_export_failed(self, error: str) -> None:
        self.export_failed.emit(error)
        logger.error(f"视频导出失败: {error}")
        if self._export_worker:
            self._export_worker.deleteLater()
            self._export_worker = None
