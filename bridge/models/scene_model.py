"""场次列表模型，供 QML ListView 使用。"""

from __future__ import annotations

from PySide6.QtCore import QAbstractListModel, QModelIndex, Property, Qt, Signal

from models.scene import Scene


class SceneListModel(QAbstractListModel):
    IdRole = Qt.UserRole + 1
    SceneNumberRole = Qt.UserRole + 2
    LocationRole = Qt.UserRole + 3
    TimeOfDayRole = Qt.UserRole + 4
    ContentRole = Qt.UserRole + 5
    LocationTypeRole = Qt.UserRole + 6
    TimeTypeRole = Qt.UserRole + 7
    TimeDetailRole = Qt.UserRole + 8

    _ROLE_NAMES = {
        IdRole: b"sceneId",
        SceneNumberRole: b"sceneNumber",
        LocationRole: b"location",
        TimeOfDayRole: b"timeOfDay",
        ContentRole: b"content",
        LocationTypeRole: b"locationType",
        TimeTypeRole: b"timeType",
        TimeDetailRole: b"timeDetail",
    }

    count_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: list[Scene] = []

    def roleNames(self):
        return self._ROLE_NAMES

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    @Property(int, notify=count_changed)
    def count(self):
        """返回模型中的数据条数，供 QML 使用。"""
        return len(self._data)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self._data):
            return None
        item = self._data[index.row()]
        if role == self.IdRole:
            return item.id
        if role == self.SceneNumberRole:
            return item.scene_number
        if role == self.LocationRole:
            return item.location
        if role == self.TimeOfDayRole:
            return item.time_type.value
        if role == self.ContentRole:
            return item.content
        if role == self.LocationTypeRole:
            return item.location_type.value
        if role == self.TimeTypeRole:
            return item.time_type.value
        if role == self.TimeDetailRole:
            return item.time_detail
        return None

    def reset(self, scenes: list[Scene]) -> None:
        self.beginResetModel()
        self._data = list(scenes)
        self.endResetModel()
        self.count_changed.emit()

    def get_by_index(self, row: int) -> Scene | None:
        if 0 <= row < len(self._data):
            return self._data[row]
        return None
