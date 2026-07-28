"""消息列表模型，供 QML ListView 使用。"""

from __future__ import annotations

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt

from models.message import Message


def _format_msg_time(dt) -> str:
    """格式化消息时间（今天显示 HH:MM，其他显示 MM-DD HH:MM）。"""
    from datetime import datetime
    if not isinstance(dt, datetime):
        return str(dt)
    now = datetime.now()
    if dt.date() == now.date():
        return dt.strftime("%H:%M")
    return dt.strftime("%m-%d %H:%M")


class MessageListModel(QAbstractListModel):
    IdRole = Qt.UserRole + 1
    RoleRole = Qt.UserRole + 2
    ContentRole = Qt.UserRole + 3
    StatusRole = Qt.UserRole + 4
    LocalPathRole = Qt.UserRole + 5
    TimestampRole = Qt.UserRole + 6
    DurationRole = Qt.UserRole + 7
    WidthRole = Qt.UserRole + 8
    HeightRole = Qt.UserRole + 9
    TaskIdRole = Qt.UserRole + 10
    ErrorRole = Qt.UserRole + 11

    _ROLE_NAMES = {
        IdRole: b"msgId",
        RoleRole: b"msgRole",
        ContentRole: b"content",
        StatusRole: b"status",
        LocalPathRole: b"localPath",
        TimestampRole: b"timestamp",
        DurationRole: b"duration",
        WidthRole: b"videoWidth",
        HeightRole: b"videoHeight",
        TaskIdRole: b"taskId",
        ErrorRole: b"errorMessage",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: list[Message] = []
        self._meta: dict[str, dict] = {}  # msg_id -> {duration, width, height}

    def roleNames(self):
        return self._ROLE_NAMES

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self._data):
            return None
        msg = self._data[index.row()]
        meta = self._meta.get(msg.id, {})
        if role == self.IdRole:
            return msg.id
        if role == self.RoleRole:
            return msg.role
        if role == self.ContentRole:
            return msg.content
        if role == self.StatusRole:
            return msg.status.value
        if role == self.LocalPathRole:
            return msg.local_path
        if role == self.TimestampRole:
            return _format_msg_time(msg.created_at)
        if role == self.DurationRole:
            return meta.get("duration", 0.0)
        if role == self.WidthRole:
            return meta.get("width", 0)
        if role == self.HeightRole:
            return meta.get("height", 0)
        if role == self.TaskIdRole:
            return msg.task_id
        if role == self.ErrorRole:
            return msg.error_message
        return None

    def reset(self, messages: list[Message], meta: dict[str, dict] | None = None) -> None:
        self.beginResetModel()
        self._data = list(messages)
        self._meta = meta or {}
        self.endResetModel()

    def append(self, msg: Message, meta: dict | None = None) -> None:
        pos = len(self._data)
        self.beginInsertRows(QModelIndex(), pos, pos)
        self._data.append(msg)
        if meta:
            self._meta[msg.id] = meta
        self.endInsertRows()

    def update_status(self, msg_id: str, status: str, local_path: str = "", error: str = "") -> None:
        for i, m in enumerate(self._data):
            if m.id == msg_id:
                from models.enums import MessageStatus
                m.status = MessageStatus(status)
                if local_path:
                    m.local_path = local_path
                if error:
                    m.error_message = error
                idx = self.index(i)
                self.dataChanged.emit(idx, idx, [self.StatusRole, self.LocalPathRole, self.ErrorRole])
                return

    def set_meta(self, msg_id: str, duration: float, width: int, height: int) -> None:
        self._meta[msg_id] = {"duration": duration, "width": width, "height": height}
        for i, m in enumerate(self._data):
            if m.id == msg_id:
                idx = self.index(i)
                self.dataChanged.emit(idx, idx, [self.DurationRole, self.WidthRole, self.HeightRole])
                return
