from __future__ import annotations

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt

from models.conversation import Conversation


def _format_conv_time(dt) -> str:
    from datetime import datetime
    if not isinstance(dt, datetime):
        return str(dt)
    now = datetime.now()
    if dt.date() == now.date():
        return dt.strftime("%H:%M")
    return dt.strftime("%Y-%m-%d %H:%M")


class ConversationListModel(QAbstractListModel):
    IdRole = Qt.UserRole + 1
    TitleRole = Qt.UserRole + 2
    TimeRole = Qt.UserRole + 3

    _ROLE_NAMES = {
        IdRole: b"convId",
        TitleRole: b"title",
        TimeRole: b"timeText",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: list[Conversation] = []

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
        if role == self.TitleRole:
            return item.title
        if role == self.TimeRole:
            return _format_conv_time(item.created_at)
        return None

    def reset(self, conversations: list[Conversation]) -> None:
        self.beginResetModel()
        self._data = list(conversations)
        self.endResetModel()

    def add(self, conv: Conversation, at_top: bool = True) -> None:
        pos = 0 if at_top else len(self._data)
        self.beginInsertRows(QModelIndex(), pos, pos)
        self._data.insert(pos, conv)
        self.endInsertRows()

    def remove_by_id(self, conv_id: str) -> None:
        for i, c in enumerate(self._data):
            if c.id == conv_id:
                self.beginRemoveRows(QModelIndex(), i, i)
                self._data.pop(i)
                self.endRemoveRows()
                return

    def update_title(self, conv_id: str, title: str) -> None:
        for i, c in enumerate(self._data):
            if c.id == conv_id:
                c.title = title
                idx = self.index(i)
                self.dataChanged.emit(idx, idx, [self.TitleRole])
                return
