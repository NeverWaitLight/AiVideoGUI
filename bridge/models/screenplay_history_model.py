from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt


class ScreenplayHistoryListModel(QAbstractListModel):
    CreatedAtRole = Qt.UserRole + 1
    SceneCountRole = Qt.UserRole + 2
    DisplayTimeRole = Qt.UserRole + 3

    _ROLE_NAMES = {
        CreatedAtRole: b"createdAt",
        SceneCountRole: b"sceneCount",
        DisplayTimeRole: b"displayTime",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: list[tuple[int, int]] = []

    def roleNames(self):
        return self._ROLE_NAMES

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self._data):
            return None
        ts, count = self._data[index.row()]
        if role == self.CreatedAtRole:
            return ts
        if role == self.SceneCountRole:
            return count
        if role == self.DisplayTimeRole:
            dt = datetime.fromtimestamp(ts / 1000)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        return None

    def reset(self, items: list[tuple[int, int]]) -> None:
        self.beginResetModel()
        self._data = list(items)
        self.endResetModel()
