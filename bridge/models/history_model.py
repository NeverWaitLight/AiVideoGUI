"""通用历史版本列表模型，供 QML ListView 使用。"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt

from utils.time_format import format_timestamp_short


def _format_history_time(ts) -> str:
    """格式化历史时间，兼容 int 时间戳和 datetime 对象。"""
    from datetime import datetime
    if isinstance(ts, int):
        return format_timestamp_short(ts)
    if isinstance(ts, datetime):
        return ts.strftime("%Y-%m-%d %H:%M")
    return str(ts)


class HistoryListModel(QAbstractListModel):
    IdRole = Qt.UserRole + 1
    CreatedAtRole = Qt.UserRole + 2
    PreviewTextRole = Qt.UserRole + 3

    _ROLE_NAMES = {
        IdRole: b"historyId",
        CreatedAtRole: b"createdAt",
        PreviewTextRole: b"previewText",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: list[Any] = []

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
        if role == self.CreatedAtRole:
            return _format_history_time(item.created_at)
        if role == self.PreviewTextRole:
            # 尝试从常见字段获取预览文本
            for attr in ("content", "visual_content", "description", "name"):
                val = getattr(item, attr, "")
                if val:
                    return val[:80]
            return ""
        return None

    def reset(self, history_items: list[Any]) -> None:
        self.beginResetModel()
        self._data = list(history_items)
        self.endResetModel()

    def get_by_index(self, row: int) -> Any | None:
        if 0 <= row < len(self._data):
            return self._data[row]
        return None
