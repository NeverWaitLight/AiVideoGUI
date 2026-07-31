from __future__ import annotations

from loguru import logger

from PySide6.QtCore import QObject, Property, Signal, Slot

from bridge.models.media_file_model import MediaFileListModel


class MediaBridge(QObject):
    files_changed = Signal()

    def __init__(self, media_service, parent=None):
        super().__init__(parent)
        self._media_service = media_service
        self._model = MediaFileListModel(self)

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
