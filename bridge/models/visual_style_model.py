from __future__ import annotations

import os
from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt

from models.visual_style import VisualStyle
from utils.time_format import format_timestamp_short
from utils import paths


class VisualStyleListModel(QAbstractListModel):
    IdRole = Qt.UserRole + 1
    NameRole = Qt.UserRole + 2
    IsDefaultRole = Qt.UserRole + 3
    SampleImagePathRole = Qt.UserRole + 4
    CreatedAtRole = Qt.UserRole + 5

    _ROLE_NAMES = {
        IdRole: b"styleId",
        NameRole: b"name",
        IsDefaultRole: b"isDefault",
        SampleImagePathRole: b"sampleImagePath",
        CreatedAtRole: b"createdAt",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: list[VisualStyle] = []
        workspace_root = paths.workspace_root()
        self._workspace_dir = paths.workspace_dir(workspace_root)

    def roleNames(self):
        return self._ROLE_NAMES

    def rowCount(self, parent=QModelIndex()):
        return len(self._data) + 1  # +1 for "默认" option

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or index.row() >= self.rowCount():
            return None

        # First item is "默认" option
        if index.row() == 0:
            if role == self.IdRole:
                return -1  # Special ID for default option
            if role == self.NameRole:
                return "默认"
            if role == self.IsDefaultRole:
                return False
            if role == self.SampleImagePathRole:
                return ""
            if role == self.CreatedAtRole:
                return ""
            return None

        # Other items are actual styles
        item = self._data[index.row() - 1]
        if role == self.IdRole:
            return item.id
        if role == self.NameRole:
            return item.name
        if role == self.IsDefaultRole:
            return item.is_default
        if role == self.SampleImagePathRole:
            if item.sample_image_path:
                abs_path = os.path.join(self._workspace_dir, item.sample_image_path)
                return abs_path.replace('\\', '/')
            return ""
        if role == self.CreatedAtRole:
            return format_timestamp_short(item.created_at)
        return None

    def reset(self, styles: list[VisualStyle]) -> None:
        self.beginResetModel()
        self._data = list(styles)
        self.endResetModel()
