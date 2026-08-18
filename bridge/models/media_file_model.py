from __future__ import annotations

from PySide6.QtCore import QAbstractListModel, QModelIndex, Property, Signal, Qt

from models.media_file import MediaFile


class MediaFileListModel(QAbstractListModel):
    IdRole = Qt.UserRole + 1
    FileNameRole = Qt.UserRole + 2
    FileTypeRole = Qt.UserRole + 3
    FilePathRole = Qt.UserRole + 4
    ThumbnailRole = Qt.UserRole + 5
    FirstFrameRole = Qt.UserRole + 11
    LastFrameRole = Qt.UserRole + 12
    DurationRole = Qt.UserRole + 6
    WidthRole = Qt.UserRole + 7
    HeightRole = Qt.UserRole + 8
    FileSizeRole = Qt.UserRole + 9
    StoryboardIdRole = Qt.UserRole + 10

    _ROLE_NAMES = {
        IdRole: b"fileId",
        FileNameRole: b"fileName",
        FileTypeRole: b"fileType",
        FilePathRole: b"filePath",
        ThumbnailRole: b"thumbnailPath",
        FirstFrameRole: b"firstFramePath",
        LastFrameRole: b"lastFramePath",
        DurationRole: b"duration",
        WidthRole: b"videoWidth",
        HeightRole: b"videoHeight",
        FileSizeRole: b"fileSize",
        StoryboardIdRole: b"storyboardId",
    }

    countChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: list[MediaFile] = []

    @Property(int, notify=countChanged)
    def count(self):
        return len(self._data)

    def roleNames(self):
        return self._ROLE_NAMES

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self._data):
            return None
        item = self._data[index.row()]
        if role == self.IdRole:
            return item.id
        if role == self.FileNameRole:
            return item.filename
        if role == self.FileTypeRole:
            return item.media_type.value
        if role == self.FilePathRole:
            return item.local_path
        if role == self.ThumbnailRole:
            return item.thumbnail_path
        if role == self.FirstFrameRole:
            return item.first_frame_path
        if role == self.LastFrameRole:
            return item.last_frame_path
        if role == self.DurationRole:
            return item.duration
        if role == self.WidthRole:
            return item.width
        if role == self.HeightRole:
            return item.height
        if role == self.FileSizeRole:
            return item.file_size
        if role == self.StoryboardIdRole:
            return item.storyboard_id
        return None

    def reset(self, files: list[MediaFile]) -> None:
        self.beginResetModel()
        self._data = list(files)
        self.endResetModel()
        self.countChanged.emit()

    def remove_by_id(self, file_id: str) -> None:
        for i, f in enumerate(self._data):
            if f.id == file_id:
                self.beginRemoveRows(QModelIndex(), i, i)
                self._data.pop(i)
                self.endRemoveRows()
                self.countChanged.emit()
                return
